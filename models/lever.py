from db import get_connection

class Lever:
    def __init__(self):
        self.load_state()

    def load_state(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM lever_state LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        self.position = row["position"]
        self.heat = row["heat"]
        self.sealed = row["sealed"]
        self.paused = row["paused"]

    def save_state(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE lever_state
            SET position=%s, heat=%s, sealed=%s, paused=%s
        """, (self.position, self.heat, self.sealed, self.paused))
        conn.commit()
        cursor.close()
        conn.close()

    def pull_up(self):
        if self.paused:
            return "Cannot pull up, lever is paused"

        self.position = "UP"
        self.heat += 5
        self.sealed = False
        self.save_state()
        return "Lever pulled UP"

    def pull_down(self):
        if self.paused:
            return "Cannot pull down, lever is paused"

        self.position = "DOWN"
        self.heat += 5
        self.sealed = False
        self.save_state()
        return "Lever pulled DOWN"

    def seal(self):
        if self.paused:
            return "Cannot seal, lever is paused"

        self.sealed = True
        self.save_state()
        return "Sealing completed"

    def pause(self):
        self.paused = True
        self.save_state()
        return "Lever paused"

    def resume(self):
        self.paused = False
        self.save_state()
        return "Lever resumed"

    def state(self):
        return {
            "position": self.position,
            "heat": self.heat,
            "sealed": self.sealed,
            "paused": self.paused
        }

