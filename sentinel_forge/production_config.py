"""Secret-free production Courier configuration contract."""
from dataclasses import dataclass,asdict
from .enrollment import EnrollmentError

FORMAT="sentinel-courier-production-config-v1"
@dataclass(frozen=True)
class ProductionTransportConfig:
 format:str
 peer_identity:str
 peer_role:str
 endpoint_reference:str
 credential_reference:str
 protection_provider_reference:str
 network_provider_reference:str
 policy_reference:str
 enabled:bool=False
 def as_dict(self):return asdict(self)

def build_production_config(**values)->ProductionTransportConfig:
 forbidden={"secret","password","token","private_key","key_material","credential_material"}
 if forbidden & set(values):raise EnrollmentError("production configuration must not contain secret material")
 required=("peer_identity","peer_role","endpoint_reference","credential_reference","protection_provider_reference","network_provider_reference","policy_reference")
 for k in required:
  v=values.get(k)
  if not isinstance(v,str) or not v.strip():raise EnrollmentError(f"production configuration {k} required")
 enabled=values.get("enabled",False)
 if enabled is not False:raise EnrollmentError("production configuration cannot be born enabled")
 extra=set(values)-set(required)-{"enabled"}
 if extra:raise EnrollmentError("production configuration contains unknown fields")
 return ProductionTransportConfig(FORMAT,*(values[k] for k in required),False)
