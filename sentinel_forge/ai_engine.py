"""Standalone Forge operator AI orchestration boundary.

Model output proposes responses/actions. Tool policy remains authoritative.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol
from .enrollment import EnrollmentError

class ModelProvider(Protocol):
 provider_id:str
 def respond(self,command:str,context:str)->str:...

@dataclass(frozen=True)
class ToolResult:
 tool:str;ok:bool;summary:str;evidence:tuple[str,...]=()

@dataclass(frozen=True)
class AiResponse:
 provider_id:str;command:str;response:str;tool_results:tuple[ToolResult,...]

class Tool:
 def __init__(self,name,handler,*,mutating=False):
  if not isinstance(name,str) or not name.strip() or not callable(handler):raise EnrollmentError("AI tool invalid")
  self.name=name;self.handler=handler;self.mutating=bool(mutating)

class ForgeAiEngine:
 def __init__(self,provider:ModelProvider,tools=()):
  if provider is None or not isinstance(getattr(provider,"provider_id",None),str):raise EnrollmentError("AI model provider required")
  self.provider=provider;self.tools={}
  for t in tools:
   if not isinstance(t,Tool) or t.name in self.tools:raise EnrollmentError("AI tool registry invalid")
   self.tools[t.name]=t
 def ask(self,command,*,context=""):
  if not isinstance(command,str) or not command.strip():raise EnrollmentError("operator command required")
  out=self.provider.respond(command,context)
  if not isinstance(out,str) or not out.strip():raise EnrollmentError("AI provider returned invalid response")
  return AiResponse(self.provider.provider_id,command,out,())
 def execute_tool(self,name,args,*,operator_approved=False):
  if name not in self.tools:raise EnrollmentError("AI tool not allowlisted")
  t=self.tools[name]
  if t.mutating and operator_approved is not True:raise EnrollmentError("mutating AI tool requires operator approval")
  r=t.handler(args)
  if not isinstance(r,ToolResult) or r.tool!=name:raise EnrollmentError("AI tool returned invalid result")
  return r

class UnavailableLocalModel:
 provider_id="local-model-unavailable"
 def respond(self,command,context):
  raise EnrollmentError("standalone local model runtime/model is not installed")
