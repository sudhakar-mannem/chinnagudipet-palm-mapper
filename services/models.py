"""Shared data models and geo clustering."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# Photos within this distance of a plant icon are shown together on click.
DEFAULT_PHOTO_RADIUS_M = 4.0


@dataclass
class PlantObservation:
    """One analyzed plant photo observation."""

    file_id: str
    file_name: str
    local_path: str
    modified_time: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PlantObservation":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)


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


def cluster_by_radius(
    observations: List[PlantObservation],
    radius_m: float = DEFAULT_PHOTO_RADIUS_M,
) -> List[PlantCluster]:
    """
    Cluster photos by location.

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
