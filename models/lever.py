from db import get_connection

class Lever:
    LOWER_LIMIT = 40
    UPPER_LIMIT = 50

    def __init__(self):
        self.position = "DOWN"
        self.heat = 40
        self.sealed = False
        self.paused = False

        self.load_state()

    def load_state(self):
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM lever_state LIMIT 1")
        row = cursor.fetchone()

        if row:
            self.position = row["position"]
            self.heat = row["heat"]
            self.sealed = row["sealed"]
            self.paused = row["paused"]

        cursor.close()
        conn.close()

    def save_state(self):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM lever_state")

        cursor.execute("""
            INSERT INTO lever_state (position, heat, sealed, paused)
            VALUES (%s, %s, %s, %s)
        """, (self.position, self.heat, self.sealed, self.paused))

        conn.commit()
        cursor.close()
        conn.close()

    def pull_up(self):
        if self.paused:
            return "System is paused"

        if self.heat >= self.UPPER_LIMIT:
            return "Upper heat limit reached"

        self.position = "UP"
        self.sealed = True
        self.heat += 5

        if self.heat > self.UPPER_LIMIT:
            self.heat = self.UPPER_LIMIT

        self.save_state()
        return "Lever pulled UP"

    def pull_down(self):
        if self.paused:
            return "System is paused"

        if self.heat <= self.LOWER_LIMIT:
            return "Lower heat limit reached"

        self.position = "DOWN"
        self.sealed = False
        self.heat -= 5

        if self.heat < self.LOWER_LIMIT:
            self.heat = self.LOWER_LIMIT

        self.save_state()
        return "Lever pulled DOWN"

    def pause(self):
        self.paused = True
        self.save_state()
        return "System paused"

    def resume(self):
        self.paused = False
        self.save_state()
        return "System resumed"

    def state(self):
        return {
            "position": self.position,
            "heat": self.heat,
            "sealed": self.sealed,
            "paused": self.paused
        }

