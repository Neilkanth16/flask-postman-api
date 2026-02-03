from states import LeverState, LeverEvent, TransitionResult
from typing import Callable, Dict, Tuple, Optional, List
import logging

logger = logging.getLogger(__name__)

class StateMachine:    
    def __init__(self, initial_state: LeverState):
        self.current_state = initial_state
        self.previous_state = None
        
        self.transitions: Dict[Tuple[LeverState, LeverEvent], Tuple[LeverState, Optional[Callable]]] = {}
        
        self.on_enter: Dict[LeverState, List[Callable]] = {}
        self.on_exit: Dict[LeverState, List[Callable]] = {}
        
        self.guards: Dict[Tuple[LeverState, LeverEvent], Callable] = {}
        
    def add_transition(
        self, 
        from_state: LeverState, 
        event: LeverEvent, 
        to_state: LeverState, 
        action: Optional[Callable] = None,
        guard: Optional[Callable] = None
    ):
        self.transitions[(from_state, event)] = (to_state, action)
        if guard:
            self.guards[(from_state, event)] = guard
            
    def add_on_enter(self, state: LeverState, callback: Callable):
        if state not in self.on_enter:
            self.on_enter[state] = []
        self.on_enter[state].append(callback)
        
    def add_on_exit(self, state: LeverState, callback: Callable):
        if state not in self.on_exit:
            self.on_exit[state] = []
        self.on_exit[state].append(callback)
    
    def can_transition(self, event: LeverEvent) -> bool:
        key = (self.current_state, event)
        
        if key not in self.transitions:
            return False
            
        if key in self.guards:
            return self.guards[key]()
            
        return True
    
    def trigger(self, event: LeverEvent, context: Optional[dict] = None) -> TransitionResult:
        context = context or {}
        key = (self.current_state, event)
        
        if key not in self.transitions:
            return TransitionResult.INVALID
        
        if key in self.guards and not self.guards[key]():
            return TransitionResult.BLOCKED
        
        new_state, action = self.transitions[key]
        
        if self.current_state in self.on_exit:
            for callback in self.on_exit[self.current_state]:
                callback(context)
        
        if action:
            action(context)
        
        self.previous_state = self.current_state
        self.current_state = new_state
        
        if new_state in self.on_enter:
            for callback in self.on_enter[new_state]:
                callback(context)
        
        return TransitionResult.SUCCESS
    
    def get_state(self) -> LeverState:
        return self.current_state
    
    def get_previous_state(self) -> Optional[LeverState]:
        return self.previous_state