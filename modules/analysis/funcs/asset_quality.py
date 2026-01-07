from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import Dict, Any

def check_asset_quality(doc, production_boe: float) -> CheckResult:
    """
    Checks:
    1. Oil vs Gas Mix (High Oil % is usually preferred for value, unless Gas play).
    2. Well Location/Quality (Tier 1, Permian, etc.).
    """
    extractor = Extractor(doc)
    
    # --- 1. Product Mix ---
    # Look for "Oil Production" specifically
    oil_bundle = extractor.extract_metric("Oil Production", ["oil production", "crude oil production", "liquids production"])
    gas_bundle = extractor.extract_metric("Gas Production", ["natural gas production", "gas production"])
    
    oil_mix_pct = 0.0
    mix_status = "Unknown"
    
    if oil_bundle and oil_bundle.value_parsed > 0:
        # If units are Bbls vs Mcf vs BOE, extraction needs to be careful.
        # Assuming extracted value is normalized or we are comparing relative magnitudes roughly if units missing.
        # Ideally, we calculate based on BOE.
        # If we have total production_boe passed in:
        
        # Check if oil value is likely Bbls (1:1 BOE)
        oil_vol = oil_bundle.value_parsed
        if oil_vol > production_boe: 
            # Likely an error or units mismatch (e.g. comparing annual vs daily)
            pass
        
        oil_mix_pct = (oil_vol / production_boe) * 100
        
        if oil_mix_pct > 100: oil_mix_pct = 100 # Cap
        
    # Interpretation
    if oil_mix_pct > 50:
        mix_str = f"Oil Weighted ({oil_mix_pct:.0f}%)"
        mix_rating = Status.OK
    elif oil_mix_pct > 30:
        mix_str = f"Balanced/Gassy ({oil_mix_pct:.0f}% Oil)"
        mix_rating = Status.WATCH
    elif oil_mix_pct > 0:
        mix_str = f"Gas Heavy ({oil_mix_pct:.0f}% Oil)"
        mix_rating = Status.WATCH # Not necessarily RED, some want Gas. But usually Oil implies Tier 1 value currently.
    else:
        mix_str = "Mix Unknown"
        mix_rating = Status.NA
        
    # --- 2. Well Location / Tier 1 ---
    # Keyword search for premium basins
    text_lower = doc.full_text.lower()
    keywords = {
        "Permian": ["permian", "delaware basin", "midland basin"],
        "Bakken": ["bakken", "williston"],
        "Eagle Ford": ["eagle ford"],
        "Tier 1": ["tier 1", "premium inventory", "core acreage"]
    }
    
    found_basins = []
    for basin, keys in keywords.items():
        if any(k in text_lower for k in keys):
            found_basins.append(basin)
            
    is_tier1 = "Tier 1" in found_basins or "Permian" in found_basins
    location_status = Status.OK if is_tier1 else Status.WATCH
    
    # Combined Status
    final_status = Status.OK if (mix_rating == Status.OK and location_status == Status.OK) else Status.WATCH
    if mix_rating == Status.NA: final_status = Status.NA
    
    interpretation = f"{mix_str}. \nLocations: {', '.join(found_basins) if found_basins else 'No Core Basin Identified'}."
    
    return CheckResult(
        "Asset Quality (Mix & Location)",
        oil_mix_pct,
        final_status,
        interpretation,
        [oil_bundle] if oil_bundle else [],
        "Oil % + Basin Check"
    )
