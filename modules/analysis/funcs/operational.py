from ..validator import CheckResult, Status
from ..evidence import EvidenceBundle
from ..extractor import Extractor
from typing import List, Optional

def check_ownership_pipelines_and_water(doc) -> CheckResult:
    """
    15) check_ownership_pipelines_and_water
    Definition: Does the company own, control, or have material interest in pipelines, midstream assets, and water handling infrastructure?
    """
    extractor = Extractor(doc)
    
    # Simple keyword check
    pipeline_evidence = extractor.extract_metric("Pipelines", ["pipelines", "gathering systems", "midstream assets"])
    water_evidence = extractor.extract_metric("Water Infrastructure", ["water handling", "water disposal", "water infrastructure"])
    
    status = Status.OK if (pipeline_evidence or water_evidence) else Status.NA
    interpretation = "Ownership: "
    if pipeline_evidence: interpretation += "Pipelines/Midstream found. "
    if water_evidence: interpretation += "Water Infra found."
    if not pipeline_evidence and not water_evidence: interpretation = "No specific midstream/water assets mentions found."
    
    evidence = []
    if pipeline_evidence: evidence.append(pipeline_evidence)
    if water_evidence: evidence.append(water_evidence)
    
    return CheckResult("check_ownership_pipelines_and_water", "See Notes", status, interpretation, evidence)

def check_production_efficiency(doc, production_boe: float) -> CheckResult:
    """
    17) check_production_efficiency
    Definition: production efficiency = actual production / max potential production.
    Rule: Must be > 85%. If <= 85% then RED.
    """
    extractor = Extractor(doc)
    capacity_bundle = extractor.extract_metric("Production Capacity", ["production capacity", "nameplate capacity", "facility capacity", "potential production"])
    
    if capacity_bundle and production_boe:
        capacity = capacity_bundle.value_parsed
        if capacity > 0:
            efficiency = production_boe / capacity
            status = Status.OK if efficiency > 0.85 else Status.RED
            # Interpret > 100% as data mismatch or super-efficiency (unlikely for capacity)
            if efficiency > 1.2:
                 return CheckResult("check_production_efficiency", efficiency, Status.NA, f"Calculated efficiency {efficiency:.1%} seems disparate. Check units.", [capacity_bundle])

            return CheckResult("check_production_efficiency", efficiency, status, f"Efficiency: {efficiency:.1%}", [capacity_bundle], "Actual / Capacity")
            
    return CheckResult("check_production_efficiency", None, Status.NA, "Max capacity not disclosed.", [])

def compute_recycle_ratio(doc) -> CheckResult:
    """
    18) compute_recycle_ratio
    Definition: recycle ratio = netback per BOE / (finding_and_development_cost_per_BOE).
    Rule: Must be > 2. If <= 2 then RED.
    """
    extractor = Extractor(doc)
    evidence = []
    
    netback_bundle = extractor.extract_metric("Netback", ["netback", "realized netback"])
    fd_cost_bundle = extractor.extract_metric("F&D Cost", ["finding and development costs", "f&d costs", "finding and development"])
    
    if netback_bundle and fd_cost_bundle:
        evidence.extend([netback_bundle, fd_cost_bundle])
        netback = netback_bundle.value_parsed
        fd_cost = fd_cost_bundle.value_parsed
        
        # Ensure units. Assuming both per BOE.
        if fd_cost > 0:
            ratio = netback / fd_cost
            status = Status.OK if ratio > 2 else Status.RED
            return CheckResult("compute_recycle_ratio", ratio, status, f"Recycle Ratio: {ratio:.2f}x", evidence, "Netback / F&D Cost")
            
    return CheckResult("compute_recycle_ratio", None, Status.NA, "Missing Netback or F&D Cost.", evidence)
