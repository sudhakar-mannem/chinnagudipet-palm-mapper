"""Shared data models and geo clustering."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Photos within this distance of a plant icon are shown together on click.
DEFAULT_PHOTO_RADIUS_M = 4.0
# Target center-to-center spacing when realigning plant icons on the map / KML.
DEFAULT_PLANT_SPACING_M = 9.0

# Local ENU meters ↔ degrees (sufficient at farm scale).
_METERS_PER_DEG_LAT = 111_320.0


@dataclass
class PlantObservation:
    """One analyzed plant photo observation."""

    file_id: str
    file_name: str
    local_path: str
    modified_time: str
    # Original GPS from photo stamp / EXIF — never overwritten by realignment.
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    # Map/KML display coords after logical ~9 m lattice realignment (optional).
    display_latitude: Optional[float] = None
    display_longitude: Optional[float] = None
    health: str = "white"  # green | amber | red | white
    confidence: float = 0.0
    summary: str = ""
    issues: List[str] = field(default_factory=list)
    photo_url: str = ""
    plant_id: str = ""
    analyzed_at: str = ""
    source: str = "drive"
    source_folder_id: str = ""
    source_folder_path: str = ""
    # When True, keep observation (and original GPS) but hide from map/KML/select.
    excluded_from_map: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlantObservation":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    @property
    def map_latitude(self) -> Optional[float]:
        """Prefer realigned display position for maps/exports."""
        if self.display_latitude is not None:
            return self.display_latitude
        return self.latitude

    @property
    def map_longitude(self) -> Optional[float]:
        """Prefer realigned display position for maps/exports."""
        if self.display_longitude is not None:
            return self.display_longitude
        return self.longitude


@dataclass
class PlantCluster:
    """One map icon = latest plant status + all photos within the radius."""

    representative: PlantObservation
    members: List[PlantObservation] = field(default_factory=list)
    radius_m: float = DEFAULT_PHOTO_RADIUS_M

    @property
    def photo_count(self) -> int:
        return len(self.members)


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _meters_per_deg_lon(lat_deg: float) -> float:
    return _METERS_PER_DEG_LAT * math.cos(math.radians(lat_deg))


def _to_local_xy(
    lat: float, lon: float, origin_lat: float, origin_lon: float
) -> Tuple[float, float]:
    """East/north meters relative to origin."""
    x = (lon - origin_lon) * _meters_per_deg_lon(origin_lat)
    y = (lat - origin_lat) * _METERS_PER_DEG_LAT
    return x, y


def _from_local_xy(
    x: float, y: float, origin_lat: float, origin_lon: float
) -> Tuple[float, float]:
    """Local east/north meters → lat/lon."""
    lat = origin_lat + y / _METERS_PER_DEG_LAT
    lon = origin_lon + x / _meters_per_deg_lon(origin_lat)
    return lat, lon


def _pca_axes(points: Sequence[Tuple[float, float]]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    2-D PCA: return unit vectors (along_row, across_row).
    Along-row is the dominant farm planting direction from GPS scatter.
    """
    n = len(points)
    if n < 2:
        return (1.0, 0.0), (0.0, 1.0)
    mx = sum(p[0] for p in points) / n
    my = sum(p[1] for p in points) / n
    cxx = cyy = cxy = 0.0
    for x, y in points:
        dx, dy = x - mx, y - my
        cxx += dx * dx
        cyy += dy * dy
        cxy += dx * dy
    # Symmetric 2x2 eigen: larger eigenvalue → row axis
    trace = cxx + cyy
    det = cxx * cyy - cxy * cxy
    disc = max(0.0, trace * trace / 4.0 - det)
    lam1 = trace / 2.0 + math.sqrt(disc)
    # Eigenvector for lam1
    if abs(cxy) > 1e-12:
        vx, vy = lam1 - cyy, cxy
    elif cxx >= cyy:
        vx, vy = 1.0, 0.0
    else:
        vx, vy = 0.0, 1.0
    norm = math.hypot(vx, vy) or 1.0
    along = (vx / norm, vy / norm)
    across = (-along[1], along[0])
    return along, across


def realign_positions(
    observations: List[PlantObservation],
    spacing_m: float = DEFAULT_PLANT_SPACING_M,
    photo_radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> int:
    """
    Compute display_latitude/display_longitude so neighboring *plants* sit on a
    ~spacing_m lattice, while leaving original latitude/longitude/altitude intact.

    Why this is "logical" (not random): PCA axes from GPS → snap each plant to a
    spacing_m grid along farm orientation → spiral-resolve collisions. Relative
    neighborhood order is preserved; only GPS jitter / uneven spacing is cleaned.
    """
    if spacing_m <= 0:
        spacing_m = DEFAULT_PLANT_SPACING_M

    # Clear prior display coords so re-runs are deterministic from original GPS.
    for obs in observations:
        obs.display_latitude = None
        obs.display_longitude = None

    clusters = cluster_by_radius(observations, radius_m=photo_radius_m)
    return apply_lattice_to_clusters(clusters, spacing_m=spacing_m)


def apply_lattice_to_clusters(
    clusters: List[PlantCluster],
    spacing_m: float = DEFAULT_PLANT_SPACING_M,
    max_farm_radius_m: float = 5000.0,
) -> int:
    """
    Assign display lat/lon on an existing photo-radius cluster list.

    Why this is logical (not random scatter):
    - PCA finds the farm's dominant planting axes from original GPS.
    - Each plant snaps to the nearest spacing_m lattice cell in that frame.
    - Collisions walk a small spiral to the next free cell so neighbors stay
      ~spacing_m apart while the overall farm footprint/order is preserved.
    - Corrupt/swapped GPS (e.g. latitude≈79) is excluded from the lattice;
      those plants keep display = original coordinates.
    """
    if spacing_m <= 0:
        spacing_m = DEFAULT_PLANT_SPACING_M

    plants = [
        c
        for c in clusters
        if c.representative.latitude is not None and c.representative.longitude is not None
    ]
    if not plants:
        return 0

    # Default: display mirrors original until lattice assigns a slot
    for c in plants:
        for member in c.members:
            if member.latitude is not None and member.longitude is not None:
                member.display_latitude = float(member.latitude)
                member.display_longitude = float(member.longitude)

    lats = [float(c.representative.latitude) for c in plants]
    lons = [float(c.representative.longitude) for c in plants]
    med_lat = sorted(lats)[len(lats) // 2]
    med_lon = sorted(lons)[len(lons) // 2]

    def _inlier(lat: float, lon: float) -> bool:
        if abs(lat) > 60.0:
            return False
        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return False
        return haversine_m(lat, lon, med_lat, med_lon) <= max_farm_radius_m

    inliers = [
        c
        for c in plants
        if _inlier(float(c.representative.latitude), float(c.representative.longitude))
    ]
    if len(inliers) < 2:
        return 0

    in_lats = [float(c.representative.latitude) for c in inliers]
    in_lons = [float(c.representative.longitude) for c in inliers]
    origin_lat = sum(in_lats) / len(in_lats)
    origin_lon = sum(in_lons) / len(in_lons)

    xy = [
        _to_local_xy(lat, lon, origin_lat, origin_lon)
        for lat, lon in zip(in_lats, in_lons)
    ]
    along, across = _pca_axes(xy)

    # Preferred lattice cell + distance-to-cell (closer plants claim a cell first)
    prefs: List[Tuple[float, int, int, int, float, float]] = []
    for i, (x, y) in enumerate(xy):
        u = x * along[0] + y * along[1]
        v = x * across[0] + y * across[1]
        iu = int(round(u / spacing_m))
        iv = int(round(v / spacing_m))
        du = u - iu * spacing_m
        dv = v - iv * spacing_m
        prefs.append((math.hypot(du, dv), i, iu, iv, u, v))
    prefs.sort(key=lambda t: t[0])

    occupied: Dict[Tuple[int, int], int] = {}

    def _spiral_free(iu: int, iv: int) -> Tuple[int, int]:
        if (iu, iv) not in occupied:
            return iu, iv
        # Expand ring until a free lattice cell is found
        for ring in range(1, max(len(inliers), 8)):
            for di in range(-ring, ring + 1):
                for dj in (-ring, ring):
                    cell = (iu + di, iv + dj)
                    if cell not in occupied:
                        return cell
            for dj in range(-ring + 1, ring):
                for di in (-ring, ring):
                    cell = (iu + di, iv + dj)
                    if cell not in occupied:
                        return cell
        # Extremely dense fallback
        k = 0
        while True:
            k += 1
            cell = (iu + k, iv)
            if cell not in occupied:
                return cell

    for _dist, i, iu, iv, _u, _v in prefs:
        cell = _spiral_free(iu, iv)
        occupied[cell] = i
        u_new = cell[0] * spacing_m
        v_new = cell[1] * spacing_m
        x = u_new * along[0] + v_new * across[0]
        y = u_new * along[1] + v_new * across[1]
        dlat, dlon = _from_local_xy(x, y, origin_lat, origin_lon)
        cluster = inliers[i]
        for member in cluster.members:
            member.display_latitude = dlat
            member.display_longitude = dlon
        cluster.representative.display_latitude = dlat
        cluster.representative.display_longitude = dlon

    return len(inliers)


def cluster_by_radius(
    observations: List[PlantObservation],
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> List[PlantCluster]:
    """
    Cluster photos by location using *original* GPS (not display positions).

    Newest photos seed cluster centers. Older photos within radius_m join that
    cluster. Same plant_id always joins the same cluster when present.
    """
    with_coords = [
        o for o in observations if o.latitude is not None and o.longitude is not None
    ]
    # Newest first so representatives are the latest health reading
    with_coords.sort(key=lambda o: o.modified_time or "", reverse=True)

    clusters: List[PlantCluster] = []
    plant_id_to_idx: Dict[str, int] = {}

    for obs in with_coords:
        placed = False
        if obs.plant_id and obs.plant_id in plant_id_to_idx:
            clusters[plant_id_to_idx[obs.plant_id]].members.append(obs)
            placed = True
        else:
            for idx, cluster in enumerate(clusters):
                rep = cluster.representative
                if haversine_m(
                    float(obs.latitude),
                    float(obs.longitude),
                    float(rep.latitude),
                    float(rep.longitude),
                ) <= radius_m:
                    cluster.members.append(obs)
                    if obs.plant_id and obs.plant_id not in plant_id_to_idx:
                        plant_id_to_idx[obs.plant_id] = idx
                    placed = True
                    break
        if not placed:
            clusters.append(
                PlantCluster(representative=obs, members=[obs], radius_m=radius_m)
            )
            if obs.plant_id:
                plant_id_to_idx[obs.plant_id] = len(clusters) - 1

    # Keep members newest-first
    for cluster in clusters:
        cluster.members.sort(key=lambda o: o.modified_time or "", reverse=True)
        cluster.representative = cluster.members[0]
    return clusters


def observation_excluded_from_map(
    obs: PlantObservation,
    excluded_file_ids: Optional[Sequence[str]] = None,
) -> bool:
    """True when this photo should not appear on Map View / consolidated exports."""
    if obs.excluded_from_map:
        return True
    if excluded_file_ids and obs.file_id and obs.file_id in excluded_file_ids:
        return True
    return False


def filter_map_observations(
    observations: Sequence[PlantObservation],
    excluded_file_ids: Optional[Sequence[str]] = None,
) -> List[PlantObservation]:
    """Drop map outliers while retaining them in stored state."""
    return [
        o
        for o in observations
        if not observation_excluded_from_map(o, excluded_file_ids=excluded_file_ids)
    ]


def group_latest_by_plant(
    observations: List[PlantObservation],
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> List[PlantObservation]:
    """Keep the newest photo per ~radius_m plant cluster (for map points)."""
    return [c.representative for c in cluster_by_radius(observations, radius_m=radius_m)]


def photos_near(
    center: PlantObservation,
    observations: List[PlantObservation],
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> List[PlantObservation]:
    """All photos within radius_m of center, newest first."""
    if center.latitude is None or center.longitude is None:
        return [center]
    nearby = []
    for obs in observations:
        if obs.latitude is None or obs.longitude is None:
            continue
        if haversine_m(
            float(center.latitude),
            float(center.longitude),
            float(obs.latitude),
            float(obs.longitude),
        ) <= radius_m:
            nearby.append(obs)
    nearby.sort(key=lambda o: o.modified_time or "", reverse=True)
    return nearby or [center]
