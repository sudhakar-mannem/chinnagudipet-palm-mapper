"""Telugu UI strings for Palm Mapper (default app language)."""
from __future__ import annotations

from typing import Any


# Health labels used in legend, map, Near me, tables
HEALTH_LABEL_TE = {
    "green": "ఆరోగ్యంగా ఉంది",
    "amber": "దృష్టి అవసరం",
    "red": "తీవ్రం / వ్యాధి",
    "white": "తెలియదు",
}

STRINGS = {
    # App / nav
    "app_title": "పామ్ మ్యాపర్",
    "menu": "మెను",
    "page_map": "మ్యాప్ వీక్షణ",
    "page_near": "నా దగ్గర",
    "page_mapping": "మొక్కల మ్యాపింగ్",
    "legend": "సూచిక",
    "drive_connected": "కనెక్ట్ అయింది",
    "drive_not_connected": "కనెక్ట్ కాలేదు",
    "drive_secrets_caption": "డ్రైవ్: %s (సీక్రెట్స్)",
    "connect_from_secrets": "సీక్రెట్స్ నుండి కనెక్ట్",
    "disconnect": "డిస్‌కనెక్ట్",
    "plant_option": "#%d | %s | %s | %d ఫోటో(లు)",
    "acc_suffix": " · GPS ±%.0f మీ",
    "altitude_m": "%.1f మీ",
    "map_photos_need_secrets": (
        "ఫోటోలకు **Streamlit Cloud Secrets**‌లో చెల్లుబాటు అయ్యే డ్రైవ్ టోకెన్ కావాలి "
        "(ఇది Palm Mapper యాప్ లోపలి మెను కాదు)."
    ),
    "how_open_secrets_steps": (
        "1. [https://share.streamlit.io](https://share.streamlit.io) తెరిచి సైన్ ఇన్ చేయండి  \n"
        "2. మీ వర్క్‌స్పేస్‌లో **chinnagudipet-palm-mapper** కనుగొనండి  \n"
        "3. యాప్‌పై **⋮** మెను → **Settings**  \n"
        "   (లేదా లైవ్ యాప్ → కుడి-కింది **Manage app** → **Settings**)  \n"
        "4. **Secrets** ట్యాబ్ తెరవండి  \n"
        "5. మీ PC ఫైల్ నుండి రెండు లైన్లు పేస్ట్ చేయండి  \n"
        "   `palm_mapper/.streamlit/secrets_cloud_snippet.toml`  \n"
        "   (`GOOGLE_CREDENTIALS_B64` మరియు `GOOGLE_TOKEN_B64`)  \n"
        "6. **Save**, తర్వాత **Reboot app**  \n"
        "7. Palm Mapper‌లో → **మొక్కల మ్యాపింగ్** → **సీక్రెట్స్ నుండి కనెక్ట్**"
    ),
    "gps_requesting_html": "ఖచ్చితమైన GPS అభ్యర్థిస్తోంది… ఫోన్ బయట ఉంచండి.",
    "gps_no_geolocation": "ఈ బ్రౌజర్‌లో లొకేషన్ లేదు.",
    "gps_lock_good": "మంచి లాక్, వర్తింపజేస్తోంది…",
    "gps_lock_wait": "మెరుగైన లాక్ కోసం వేచి ఉంది…",
    "gps_error_prefix": "GPS లోపం: ",
    "gps_coarse_fail": (
        "ఖచ్చితమైన GPS రాలేదు (ఇప్పటికీ ±%.0f మీ). "
        "మొక్క సంఖ్యకు సుమారు ±10 మీ కావాలి."
    ),
    "gps_phone_tips": (
        "**ఫోన్ సెట్టింగ్‌లు (ముఖ్యం):**\n\n"
        "1. **లొకేషన్ ON** చేయండి\n"
        "2. Android: **Location → Location accuracy / Google Location Accuracy → ON** "
        "(Precise / High accuracy)\n"
        "3. iPhone: **Settings → Privacy → Location Services → Precise Location → ON** "
        "(Safari/Chrome కోసం)\n"
        "4. బయట నిలబడి ఆకాశం కనిపించేలా ఉంచండి; Wi‑Fi మాత్రమే కాదు\n"
        "5. మళ్లీ **ఖచ్చితమైన GPS తీసుకోండి** నొక్కండి"
    ),
    "gps_howto": (
        "మొక్క పక్కన బయట నిలబడండి → ఫోన్‌లో **Precise / High accuracy** లొకేషన్ ఆన్ చేయండి → "
        "**ఖచ్చితమైన GPS తీసుకోండి** నొక్కండి → **±10 మీ** వచ్చే వరకు వేచి ఉండండి "
        "(±200–2000 మీ అంటే ఇంకా సెల్ టవర్ లొకేషన్)."
    ),
    "this_run_kml": "ఈ రన్ KML",
    "this_run_kmz": "ఈ రన్ KMZ",
    "consolidated_kml_btn": "కన్సాలిడేటెడ్ KML",
    "consolidated_kmz_btn": "కన్సాలిడేటెడ్ KMZ",
    "photos_in_selection": "ఎంపికలో ఫోటోలు",
    "on_map_this_run": "మ్యాప్‌లో (ఈ రన్)",
    "analyzed_now": "ఇప్పుడు విశ్లేషించినవి",
    "with_altitude": "ఎత్తుతో",
    "consolidated_plants": "కన్సాలిడేటెడ్ మొక్కలు",
    "processed_folders": "ప్రాసెస్ అయినవి: %s",
    "mapped_summary": (
        "మ్యాప్ **%d** మొక్కలు · విశ్లేషించిన **%d** · ఎత్తుతో **%d** · కన్సాలిడేటెడ్ **%d**"
    ),
    "syncing_analyzing": "సింక్ & విశ్లేషణ జరుగుతోంది…",
    "rebuilding_exports": (
        "కన్సాలిడేటెడ్ KML/KMZ రీబిల్డ్ అవుతోంది (కొన్ని నిమిషాలు పట్టవచ్చు)…"
    ),
    "rebuilt_ok": "రీబిల్డ్ **%d** మొక్కలు (%.0f మీ స్పేసింగ్) → `%s`",
    "farm_entire_root": "చిన్నగుడిపేట పొలం (మొత్తం రూట్)",
    "could_not_clear_token": "లోకల్ టోకెన్ క్లియర్ చేయలేకపోయాం: %s",
    "loading_drive_creds": "సీక్రెట్స్ నుండి Google Drive క్రెడెన్షియల్స్ లోడ్ అవుతున్నాయి…",
    "missing_creds_b64_long": (
        "సీక్రెట్స్‌లో `GOOGLE_CREDENTIALS_B64` లేదు. "
        "మీ PC‌లో `python make_cloud_secrets.py` నడిపి "
        "**Streamlit Cloud డ్యాష్‌బోర్డ్** (**Manage app → Settings → Secrets**, "
        "యాప్ లోపల కాదు)‌లో పేస్ట్ చేయండి."
    ),
    "missing_token_b64": (
        "సీక్రెట్స్‌లో `GOOGLE_TOKEN_B64` లేదు. "
        "మీ PC‌లో ఒకసారి `python auth_drive.py`, తర్వాత `python make_cloud_secrets.py` నడిపి "
        "రెండు B64 లైన్లను **Streamlit Cloud డ్యాష్‌బోర్డ్** "
        "(**Manage app → Settings → Secrets**, యాప్ లోపల కాదు)‌లో పేస్ట్ చేయండి."
    ),
    "secrets_status": "సీక్రెట్స్ స్థితి",
    "secrets_token_auth_failed": (
        "సీక్రెట్స్ టోకెన్‌తో డ్రైవ్ ఆథ్ కాలేదు (గడువు/రద్దు). "
        "PC‌లో టోకెన్ రిఫ్రెష్ చేసి Cloud Secrets అప్‌డేట్ చేయండి — యాప్ బ్రౌజర్ వాడదు."
    ),
    "drive_auth_failed": "సీక్రెట్స్ నుండి డ్రైవ్ ఆథ్ విఫలం: %s",
    # Map view
    "farm_map": "పొలం మ్యాప్",
    "farm_map_caption": (
        "మొక్క మార్కర్‌పై నొక్కి ఫోటోలు చూడండి. కొత్త డ్రైవ్ ఫోల్డర్‌ల కోసం సైడ్‌బార్‌లో "
        "**మొక్కల మ్యాపింగ్** వాడండి."
    ),
    "filter_health": "ఆరోగ్యం ప్రకారం ఫిల్టర్",
    "plants_on_map": "మ్యాప్‌లో మొక్కలు",
    "no_mapped_plants": (
        "ఇంకా మ్యాప్ మొక్కలు లేవు. డ్రైవ్ కనెక్ట్ చేసి విశ్లేషణ నడపడానికి సైడ్‌బార్‌లో "
        "**మొక్కల మ్యాపింగ్** తెరవండి."
    ),
    "no_plants_yet": "ఇంకా మొక్కలు లేవు.",
    "select_plant": "మొక్కను ఎంచుకోండి",
    "photos_n": "%d ఫోటో(లు)",
    "open_earth": "Google Earth ఫైల్స్ తెరవండి / డౌన్‌లోడ్",
    "open_consolidated_earth": "కన్సాలిడేటెడ్‌ను Google Earth‌లో తెరవండి",
    "download_kml": "కన్సాలిడేటెడ్ KML డౌన్‌లోడ్",
    "secrets_banner": (
        "డ్రైవ్ సీక్రెట్స్ సరిగ్గా ఉండే వరకు ఫోటోలు లోడ్ కావు. "
        "`.streamlit/secrets_cloud_snippet.toml` నుండి "
        "`GOOGLE_CREDENTIALS_B64` మరియు `GOOGLE_TOKEN_B64` ని "
        "**Streamlit Cloud డ్యాష్‌బోర్డ్** (యాప్ లోపల కాదు) → "
        "**Manage app → Settings → Secrets**‌లో పేస్ట్ చేసి, రీబూట్ చేసి, "
        "**సీక్రెట్స్ నుండి కనెక్ట్** నొక్కండి."
    ),
    "how_open_secrets": "సీక్రెట్స్ ఎలా తెరవాలి (Streamlit Cloud)",
    # Photo panel
    "plant_n_photos": "**%s** — %s · **%d** ఫోటో(లు) %.0f మీ లోపల",
    "altitude": "ఎత్తు: %.1f మీ",
    "map_position": "మ్యాప్ స్థానం (≈%.0f మీ గ్రిడ్): %.6f, %.6f",
    "original_gps": "అసలు GPS: %.6f, %.6f",
    "latest": "తాజా · ",
    "photo_meta": "**%s%d / %d** — `%s` · ఎత్తు %s",
    "n_a": "లేదు",
    "open_drive": "Google Drive‌లో తెరవండి",
    "could_not_decode": "చిత్రం ప్రివ్యూ డీకోడ్ కాలేదు",
    "larger_preview": "పెద్ద ప్రివ్యూ",
    "could_not_download": "ఈ ఫోటోను Drive నుండి డౌన్‌లోడ్ చేయలేకపోయాం.",
    "retry_download": "మళ్లీ డౌన్‌లోడ్ చేయండి",
    "show_more_photos": "మరిన్ని ఫోటోలు (%d మిగిలి ఉన్నాయి)",
    "show_fewer_photos": "తక్కువ ఫోటోలు చూపించు",
    "photos_missing_tip": "ఫోటోలు రాకపోతే సైడ్‌బార్‌లో Google Drive‌ను మళ్లీ కనెక్ట్ చేయండి.",
    "drive_secrets_invalid": (
        "డ్రైవ్ సీక్రెట్స్ టోకెన్ లేదు/చెల్లదు — ఫోటోలు డౌన్‌లోడ్ కావు. "
        "Cloud Secrets‌లో `GOOGLE_TOKEN_B64` సెట్ చేసి **సీక్రెట్స్ నుండి కనెక్ట్** నొక్కండి."
    ),
    "loading_photo": "Drive నుండి ఫోటో లోడ్ అవుతోంది…",
    # Near me
    "near_me_title": "నా దగ్గర",
    "near_me_caption": (
        "మొక్క పక్కన నిలబడి ఖచ్చితమైన ఫోన్ GPS వాడండి. "
        "మ్యాప్ వీక్షణ మొక్క సంఖ్యలతో సరిపోలుతుంది (≈9 మీ రియలైన్‌మెంట్ తర్వాత). "
        "(GPS v2 — అధిక ఖచ్చితత్వం)"
    ),
    "near_me_no_plants": (
        "ఇంకా మ్యాప్ మొక్కలు లేవు. సింక్ కోసం **మొక్కల మ్యాపింగ్** లేదా డేటా నిర్ధారణకు "
        "**మ్యాప్ వీక్షణ** తెరవండి."
    ),
    "get_precise_gps": "ఖచ్చితమైన GPS తీసుకోండి",
    "clear_gps": "GPS క్లియర్ / మళ్లీ ప్రయత్నించండి",
    "waiting_gps": "ఖచ్చితమైన GPS కోసం వేచి ఉంది…",
    "your_location": "మీ స్థానం: %.6f, %.6f%s",
    "gps_far_from_farm": (
        "ఈ GPS ఫిక్స్ పొలం కేంద్రం నుండి సుమారు **%.0f మీ** దూరంలో ఉంది — "
        "ఫోన్ పొలం మీద లాక్ కాలేదు (తరచుగా Wi‑Fi/సెల్ లొకేషన్). "
        "మొక్క పక్కన బయటికి వెళ్లి **ఖచ్చితమైన GPS తీసుకోండి** నొక్కి "
        "**±10 మీ** లేదా మెరుగైనది వచ్చే వరకు వేచి ఉండండి."
    ),
    "gps_accuracy_poor": (
        "GPS ఖచ్చితత్వం ఇంకా ±%.0f మీ. మొక్క సరిపోలికకు సుమారు ±10–20 మీ కావాలి. "
        "బయట **ఖచ్చితమైన GPS తీసుకోండి** మళ్లీ నొక్కి మెరుగైన లాక్ కోసం వేచి ఉండండి."
    ),
    "could_not_match": "మొక్కను సరిపోల్చలేకపోయాం.",
    "plant_word": "మొక్క",
    "m_away_health": "%.1f మీ దూరం · %s",
    "matched_uncertainty": (
        "GPS అనిశ్చితి (±%.0f మీ) లోపల సరిపోలింది. మొక్కను కళ్ళతో నిర్ధారించండి."
    ),
    "open_map_for_photos": "ఈ మొక్క సంఖ్య ఫోటోల కోసం మెనులో **మ్యాప్ వీక్షణ** తెరవండి.",
    "no_plant_within": "%.0f మీ లోపల మొక్క లేదు",
    "nearest_plant": "సమీపం: <b>#%d</b> · <b>%.1f మీ</b> · %s",
    # Plant mapping
    "mapping_title": "మొక్కల మ్యాపింగ్",
    "mapping_caption": (
        "డ్రైవ్ ప్రామాణీకరణ Streamlit సీక్రెట్స్ మాత్రమే (బ్రౌజర్ లేదు). "
        "ఫోల్డర్‌లు ఎంచుకుని ఆరోగ్యం + GPS/ఎత్తు విశ్లేషణ నడపండి."
    ),
    "metric_openai": "OpenAI కీ",
    "metric_drive_creds": "డ్రైవ్ క్రెడెన్షియల్స్",
    "metric_drive_secrets": "డ్రైవ్ (సీక్రెట్స్)",
    "metric_folder": "ఫోల్డర్ ID",
    "ready": "సిద్ధం",
    "missing": "లేదు",
    "not_ready": "సిద్ధం కాదు",
    "set": "సెట్ అయింది",
    "cloud_secrets_status": "క్లౌడ్ సీక్రెట్స్ స్థితి",
    "secrets_help": (
        "Cloud Secrets‌లో `GOOGLE_CREDENTIALS_B64` మరియు `GOOGLE_TOKEN_B64` జోడించండి "
        "(మీ PC‌లో `python make_cloud_secrets.py`), రీబూట్ చేసి **సీక్రెట్స్ నుండి కనెక్ట్** నొక్కండి. "
        "యాప్ బ్రౌజర్ లాగిన్ తెరవదు."
    ),
    "gdrive_secrets_header": "Google Drive (సీక్రెట్స్)",
    "missing_creds_b64": "సీక్రెట్స్‌లో `GOOGLE_CREDENTIALS_B64` లేదు.",
    "drive_connected_secrets": "సీక్రెట్స్ ద్వారా Google Drive కనెక్ట్ అయింది.",
    "not_ready_click_connect": "సిద్ధం కాదు — **సీక్రెట్స్ నుండి కనెక్ట్** నొక్కండి.",
    "select_folders": "1. ఫోల్డర్‌లు ఎంచుకోండి",
    "root_folder_id": "రూట్ Google Drive ఫోల్డర్ ID",
    "root_folder_help": "పై స్థాయి పామ్ ఫోటోల ఫోల్డర్.",
    "refresh_folders": "ఫోల్డర్ జాబితా రిఫ్రెష్",
    "connect_then_refresh": "ముందు **సీక్రెట్స్ నుండి కనెక్ట్**, తర్వాత ఫోల్డర్ జాబితా రిఫ్రెష్ చేయండి.",
    "click_refresh_folders": "**ఫోల్డర్ జాబితా రిఫ్రెష్** నొక్కండి.",
    "no_subfolders": "ఈ రూట్ కింద సబ్‌ఫోల్డర్‌లు కనబడలేదు.",
    "folders_to_process": "ప్రాసెస్ చేయాల్సిన ఫోల్డర్‌లు",
    "folders_selected": "%d / %d ఫోల్డర్(లు) ఎంచుకున్నారు",
    "advanced": "అధునాతన ఎంపికలు",
    "process_entire_root": "మొత్తం పొలం రూట్ (అన్ని నెస్టెడ్ ఫోటోలు) ప్రాసెస్ చేయి",
    "start_fresh": "కొత్తగా ప్రారంభించు (మునుపటి విశ్లేషణ + ఎగుమతులు క్లియర్)",
    "reanalyze": "కాష్‌లో ఉన్న ఫోటోలను మళ్లీ విశ్లేషించు",
    "force_dl": "Drive నుండి అన్ని ఫోటోలను మళ్లీ డౌన్‌లోడ్ చేయి",
    "cache_path": "కాష్: `%s`",
    "run_analysis": "2. విశ్లేషణ నడపండి",
    "sync_analyze": "సింక్ & విశ్లేషణ",
    "sync_analyze_scratch": "సింక్ & విశ్లేషణ (కొత్తగా)",
    "need_openai": "palm_mapper/.env‌లో OPENAI_API_KEY సేవ్ చేసి రిఫ్రెష్ చేయండి.",
    "need_creds_file": "ముందుగా credentials/credentials.json జోడించండి.",
    "need_folder": "కనీసం ఒక ఫోల్డర్ ఎంచుకోండి, లేదా **మొత్తం పొలం రూట్ ప్రాసెస్** ఆన్ చేయండి.",
    "exports": "ఎగుమతులు",
    "output_folder": "అవుట్‌పుట్ ఫోల్డర్: `%s`",
    "rebuild_map": "నిల్వ ఉన్న అన్ని మొక్కల నుండి కన్సాలిడేటెడ్ మ్యాప్ రీబిల్డ్",
    "plant_table": "మొక్కల పట్టిక (మొత్తం పొలం)",
    "no_obs": "ఇంకా అబ్జర్వేషన్‌లు నిల్వ కాలేదు.",
    "connected_secrets_ok": "సీక్రెట్స్ ద్వారా Google Drive కనెక్ట్ అయింది (బ్రౌజర్ లేదు).",
    "disconnected": "Google Drive నుండి డిస్‌కనెక్ట్ అయ్యారు.",
    "secrets_still_provide": (
        "లోకల్ టోకెన్ క్లియర్ అయింది, కానీ సీక్రెట్స్‌లో `GOOGLE_TOKEN_B64` ఉంది "
        "(రీలోడ్‌పై డ్రైవ్ మళ్లీ కనెక్ట్ అవుతుంది). పూర్తిగా డిస్‌కనెక్ట్ కావాలంటే ఆ సీక్రెట్ తీసేయండి."
    ),
    "popup_photos": "%d ఫోటో(లు) — ప్యానెల్ చూడండి →",
    "tooltip_photos": "%s · %d ఫోటోలు",
}


def t(key: str, *args: Any, **kwargs: Any) -> str:
    """Return Telugu UI string; supports % formatting via args/kwargs."""
    text = STRINGS.get(key, key)
    if args:
        try:
            return text % args
        except Exception:
            return text
    if kwargs:
        try:
            return text % kwargs
        except Exception:
            return text
    return text


def health_label(health: str) -> str:
    return HEALTH_LABEL_TE.get(health, HEALTH_LABEL_TE["white"])
