from db import get_connection
from fsm import StateMachine
from states import LeverState, LeverEvent, TransitionResult
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Lever:
    def __init__(self):
        self.position = 50
        self.heat = 0
        self.sealing_progress = 0
        self.db_state = "STOPPED"
        
        self.lower = 0
        self.upper = 100
        self.step = 1
        self.tick = 0.1
        self.sealing_duration = 10
        
        self.load_config()
        self.load_state()
        
        initial_state = self._db_state_to_enum(self.db_state)
        self.fsm = StateMachine(initial_state)
        
        self._setup_fsm()
        
        logger.info(f"Lever initialized: position={self.position}, state={initial_state.value}")

    def load_config(self):
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM lever_config WHERE id=1")
            cfg = cur.fetchone()

            if cfg:
                self.lower = cfg["lower_limit"]
                self.upper = cfg["upper_limit"]
                self.step = cfg["step"]
                self.tick = cfg["tick_ms"] / 1000
                self.sealing_duration = cfg["sealing_duration"]

            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error loading config: {e}")

    def load_state(self):
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM lever_state WHERE id=1")
            row = cur.fetchone()

            if row:
                self.position = float(row["position"])
                self.heat = float(row["heat"])
                self.db_state = str(row["state"])
                self.sealing_progress = int(row["sealing_progress"])

            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error loading state: {e}")

    def save_state(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE lever_state
                SET position=%s, heat=%s, state=%s, sealing_progress=%s
                WHERE id=1
            """, (self.position, self.heat, self.fsm.get_state().value, self.sealing_progress))

            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def log(self, action, details=""):
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO lever_history (action, position, heat, state, details)
                VALUES (%s, %s, %s, %s, %s)
            """, (action, self.position, self.heat, self.fsm.get_state().value, details))

            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"Error logging: {e}")

    def _setup_fsm(self):
        fsm = self.fsm
    
        fsm.add_transition(LeverState.STOPPED, LeverEvent.PULL_UP, LeverState.STARTING_UP, self._start_moving_up)
        fsm.add_transition(LeverState.STOPPED, LeverEvent.PULL_DOWN, LeverState.STARTING_DOWN, self._start_moving_down)
        fsm.add_transition(LeverState.STOPPED, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.STOPPED, LeverEvent.TICK, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.STARTING_UP, LeverEvent.TICK, LeverState.MOVING_UP, self._accelerate_up)
        fsm.add_transition(LeverState.STARTING_UP, LeverEvent.PULL_DOWN, LeverState.SLOWING_UP, self._begin_deceleration)
        fsm.add_transition(LeverState.STARTING_UP, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.STARTING_UP, LeverEvent.STOP, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.MOVING_UP, LeverEvent.TICK, LeverState.MOVING_UP, self._move_up)
        fsm.add_transition(LeverState.MOVING_UP, LeverEvent.REACHED_TOP, LeverState.AT_TOP, self._handle_reached_top)
        fsm.add_transition(LeverState.MOVING_UP, LeverEvent.PULL_DOWN, LeverState.SLOWING_UP, self._begin_deceleration)
        fsm.add_transition(LeverState.MOVING_UP, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.MOVING_UP, LeverEvent.STOP, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.SLOWING_UP, LeverEvent.TICK, LeverState.STOPPED, self._decelerate_up)
        fsm.add_transition(LeverState.SLOWING_UP, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.SLOWING_UP, LeverEvent.STOP, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.STARTING_DOWN, LeverEvent.TICK, LeverState.MOVING_DOWN, self._accelerate_down)
        fsm.add_transition(LeverState.STARTING_DOWN, LeverEvent.PULL_UP, LeverState.SLOWING_DOWN, self._begin_deceleration)
        fsm.add_transition(LeverState.STARTING_DOWN, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.STARTING_DOWN, LeverEvent.STOP, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.MOVING_DOWN, LeverEvent.TICK, LeverState.MOVING_DOWN, self._move_down)
        fsm.add_transition(LeverState.MOVING_DOWN, LeverEvent.REACHED_BOTTOM, LeverState.AT_BOTTOM, self._handle_reached_bottom)
        fsm.add_transition(LeverState.MOVING_DOWN, LeverEvent.PULL_UP, LeverState.SLOWING_DOWN, self._begin_deceleration)
        fsm.add_transition(LeverState.MOVING_DOWN, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.MOVING_DOWN, LeverEvent.STOP, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.SLOWING_DOWN, LeverEvent.TICK, LeverState.STOPPED, self._decelerate_down)
        fsm.add_transition(LeverState.SLOWING_DOWN, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.SLOWING_DOWN, LeverEvent.STOP, LeverState.STOPPED)
        
        fsm.add_transition(LeverState.AT_TOP, LeverEvent.PULL_DOWN, LeverState.STARTING_DOWN, self._start_moving_down)
        fsm.add_transition(LeverState.AT_TOP, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.AT_TOP, LeverEvent.TICK, LeverState.AT_TOP)
        
        fsm.add_transition(LeverState.AT_BOTTOM, LeverEvent.PULL_UP, LeverState.STARTING_UP, self._start_moving_up)
        fsm.add_transition(LeverState.AT_BOTTOM, LeverEvent.SEAL_CONDITIONS_MET, LeverState.SEALING, self._start_sealing)
        fsm.add_transition(LeverState.AT_BOTTOM, LeverEvent.PAUSE, LeverState.PAUSED)
        fsm.add_transition(LeverState.AT_BOTTOM, LeverEvent.TICK, LeverState.AT_BOTTOM, self._check_sealing_conditions)
        
        fsm.add_transition(LeverState.SEALING, LeverEvent.TICK, LeverState.SEALING, self._progress_sealing)
        fsm.add_transition(LeverState.SEALING, LeverEvent.SEAL_COMPLETE, LeverState.AT_BOTTOM, self._complete_sealing)
        
        fsm.add_transition(LeverState.PAUSED, LeverEvent.RESUME, LeverState.STOPPED, self._resume_from_pause)
        fsm.add_transition(LeverState.PAUSED, LeverEvent.TICK, LeverState.PAUSED)

    
    def _start_moving_up(self, context):
        self.log("START_MOVING_UP")
        
    def _start_moving_down(self, context):
        self.log("START_MOVING_DOWN")
    
    def _accelerate_up(self, context):
        self.log("ACCELERATED_UP")
        
    def _accelerate_down(self, context):
        self.log("ACCELERATED_DOWN")
    
    def _move_up(self, context):
        self.position += self.step
        if self.position >= self.upper:
            self.position = self.upper
            self.fsm.trigger(LeverEvent.REACHED_TOP)
    
    def _move_down(self, context):
        self.position -= self.step
        if self.position <= self.lower:
            self.position = self.lower
            self.fsm.trigger(LeverEvent.REACHED_BOTTOM)
    
    def _begin_deceleration(self, context):
        self.log("BEGIN_DECELERATION", f"At position {self.position}")
        
    def _decelerate_up(self, context):
        self.log("DECELERATED_FROM_UP")
        
    def _decelerate_down(self, context):
        self.log("DECELERATED_FROM_DOWN")
    
    def _handle_reached_top(self, context):
        self.log("REACHED_TOP", f"Position: {self.position}")
    
    def _handle_reached_bottom(self, context):
        self.log("REACHED_BOTTOM", f"Position: {self.position}, Heat: {self.heat}")
        self._check_sealing_conditions(context)
    
    def _check_sealing_conditions(self, context):
        if 40 <= self.heat <= 50:
            self.fsm.trigger(LeverEvent.SEAL_CONDITIONS_MET)
    
    def _start_sealing(self, context):
        self.sealing_progress = 0
        self.log("SEALING_STARTED", f"Heat: {self.heat}")
    
    def _progress_sealing(self, context):
        self.sealing_progress += 1
        if self.sealing_progress >= self.sealing_duration:
            self.fsm.trigger(LeverEvent.SEAL_COMPLETE)
    
    def _complete_sealing(self, context):
        self.log("SEALING_COMPLETED")
        self.sealing_progress = 0
    
    def _resume_from_pause(self, context):
        self.log("RESUMED", f"Position: {self.position}")
   
    def pull_up(self):
        result = self.fsm.trigger(LeverEvent.PULL_UP)
        self.save_state()
        if result == TransitionResult.SUCCESS:
            return "Moving UP"
        return f"Cannot move UP from {self.fsm.get_state().value}"
    
    def pull_down(self):
        result = self.fsm.trigger(LeverEvent.PULL_DOWN)
        self.save_state()
        if result == TransitionResult.SUCCESS:
            return "Moving DOWN"
        return f"Cannot move DOWN from {self.fsm.get_state().value}"
    
    def pause(self):
        self.fsm.trigger(LeverEvent.PAUSE)
        self.save_state()
        return f"Paused at {self.position}"
    
    def resume(self):
        self.fsm.trigger(LeverEvent.RESUME)
        self.save_state()
        return f"Resumed at {self.position}"
    
    def stop(self):
        self.fsm.trigger(LeverEvent.STOP)
        self.save_state()
        return f"Stopped at {self.position}"
    
    def tick_update(self):
        self.fsm.trigger(LeverEvent.TICK)
        self.save_state()

    def get_state(self):
        return {
            "position": round(self.position, 2),
            "heat": round(self.heat, 2),
            "state": self.fsm.get_state().value,
            "sealing_progress": self.sealing_progress,
            "at_top": self.position >= self.upper,
            "at_bottom": self.position <= self.lower
        }
    
    def get_status_message(self):
        state = self.fsm.get_state()
        messages = {
            LeverState.STOPPED: f"STOPPED at {self.position:.1f}",
            LeverState.MOVING_UP: f"Moving UP ({self.position:.1f})",
            LeverState.MOVING_DOWN: f"Moving DOWN ({self.position:.1f})",
            LeverState.SLOWING_UP: f"Slowing from UP ({self.position:.1f})",
            LeverState.SLOWING_DOWN: f"Slowing from DOWN ({self.position:.1f})",
            LeverState.STARTING_UP: f"Starting UP ({self.position:.1f})",
            LeverState.STARTING_DOWN: f"Starting DOWN ({self.position:.1f})",
            LeverState.SEALING: f"SEALING {self.sealing_progress}/{self.sealing_duration}",
            LeverState.PAUSED: f"⏸PAUSED at {self.position:.1f}",
            LeverState.AT_TOP: f"At TOP ({self.position:.1f})",
            LeverState.AT_BOTTOM: f"At BOTTOM ({self.position:.1f})"
        }
        return messages.get(state, f"Unknown: {state.value}")
    
    def _db_state_to_enum(self, db_state: str) -> LeverState:
        try:
            return LeverState[db_state]
        except KeyError:
            return LeverState.STOPPED