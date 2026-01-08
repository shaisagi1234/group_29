import mysql.connector
import re  


class DbManager:
    def __init__(self):
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'rootroot',
            'database': 'FLY_TAU'
        }

    def _get_connection(self):
        try:
            conn = mysql.connector.connect(**self.db_config)
            return conn
        except mysql.connector.Error as err:
            print(f"Error connecting to DB: {err}")
            return None

    def get_all_airports(self):
        conn = self._get_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT airport_code, city, name FROM Airports ORDER BY city")
            return cursor.fetchall()
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    def search_flights(self, origin_city, dest_city, date, passengers):
        conn = self._get_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        # שימי לב: השאילתה כאן סופרת כרטיסים לפי הטבלה המקורית שלך
        query = """
            SELECT 
                f.flight_id,
                DATE_FORMAT(f.dep_time, '%H:%i') as dep_time_formatted,
                DATE_FORMAT(f.dep_date, '%d/%m/%Y') as dep_date,
                DATE_FORMAT(DATE_ADD(TIMESTAMP(f.dep_date, f.dep_time), INTERVAL (r.duration * 60) MINUTE), '%H:%i') as arrival_time,
                CASE WHEN DATE(DATE_ADD(TIMESTAMP(f.dep_date, f.dep_time), INTERVAL (r.duration * 60) MINUTE)) > f.dep_date THEN 1 ELSE 0 END as is_next_day,
                DATE_FORMAT(DATE_ADD(TIMESTAMP(f.dep_date, f.dep_time), INTERVAL (r.duration * 60) MINUTE), '%d/%m/%Y') as arrival_full_date,
                CONCAT(FLOOR(r.duration), 'h ', ROUND((r.duration - FLOOR(r.duration)) * 60), 'm') as duration_formatted,
                f.base_price, f.status, origin.city as origin_city, 
                dest.city as dest_city, p.manufacturer as plane_model,
                (p.num_of_seats - (SELECT COUNT(*) FROM Tickets t WHERE t.flight_id = f.flight_id)) as available_seats
            FROM Flights f
            JOIN Routes r ON f.route_id = r.route_id
            JOIN Airplanes p ON f.plane_id = p.plane_id
            JOIN Airports origin ON r.origin_code = origin.airport_code
            JOIN Airports dest ON r.dest_code = dest.airport_code
            WHERE origin.city = %s AND dest.city = %s AND f.dep_date = %s AND f.status != 'Cancelled'
            HAVING available_seats >= %s
        """
        try:
            cursor.execute(query, (origin_city, dest_city, date, passengers))
            return cursor.fetchall()
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    def get_ticket_details(self, email, order_id):
        conn = self._get_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        # חיפוש לפי מספר הזמנה (order_id) ולא לפי מספר כרטיס
        query = """
            SELECT b.order_id, t.ticket_id, CONCAT(t.row_num, t.col_num) as seat, 
                f.dep_date, DATE_FORMAT(f.dep_time, '%H:%i') as dep_time,
                origin.city as origin_city, dest.city as dest_city, f.status
            FROM Bookings b
            JOIN Tickets t ON t.order_id = b.order_id
            JOIN Flights f ON t.flight_id = f.flight_id
            JOIN Routes r ON f.route_id = r.route_id
            JOIN Airports origin ON r.origin_code = origin.airport_code
            JOIN Airports dest ON r.dest_code = dest.airport_code
            WHERE b.customer_email = %s AND b.order_id = %s
        """
        try:
            cursor.execute(query, (email, order_id))
            return cursor.fetchone()
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    def get_flight_seats(self, flight_id):
        conn = self._get_connection()
        if not conn: return None, [], []
        cursor = conn.cursor(dictionary=True)
        try:
            # קבלת פרטי הטיסה כולל plane_id
            query_flight = """
                SELECT f.flight_id, f.base_price, f.plane_id, origin.city as origin, dest.city as dest, 
                       p.manufacturer, p.num_of_seats
                FROM Flights f
                JOIN Routes r ON f.route_id = r.route_id
                JOIN Airports origin ON r.origin_code = origin.airport_code
                JOIN Airports dest ON r.dest_code = dest.airport_code
                JOIN Airplanes p ON f.plane_id = p.plane_id
                WHERE f.flight_id = %s
            """
            cursor.execute(query_flight, (flight_id,))
            flight = cursor.fetchone()
            if not flight: return None, [], []

            plane_id = flight['plane_id']

            # קבלת כל המושבים הזמינים מטבלת Seats למטוס הזה
            query_all_seats = """
                SELECT CONCAT(row_num, col_num) as seat, row_num, col_num
                FROM Seats 
                WHERE plane_id = %s
                ORDER BY row_num, col_num
            """
            cursor.execute(query_all_seats, (plane_id,))
            all_seats = [row['seat'] for row in cursor.fetchall()]

            # קבלת המושבים שכבר תפוסים
            query_taken = "SELECT CONCAT(row_num, col_num) as seat FROM Tickets WHERE flight_id = %s"
            cursor.execute(query_taken, (flight_id,))
            taken_seats = [row['seat'] for row in cursor.fetchall()]

            return flight, taken_seats, all_seats
        except Exception as e:
            print(f"Error: {e}")
            return None, [], []
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    def add_ticket(self, flight_id, seat_str, email, first_name, last_name):
        """
        הפונקציה הזו עושה את העבודה הקשה:
        1. מפרקת את המושב (למשל '20A') לשורה (20) וטור (A)
        2. יוצרת הזמנה (Booking)
        3. יוצרת כרטיס (Ticket) שמקושר להזמנה
        """
        conn = self._get_connection()
        if not conn: 
            print("DB Connection failed")
            return False
        cursor = conn.cursor()

        try:
            # שלב 1: פירוק המושב (Regex)
            print(f"DEBUG: Trying to book seat '{seat_str}' for flight {flight_id}")
            
            # מחפש מספרים ואז אותיות
            match = re.match(r"(\d+)([A-Z])", seat_str.strip().upper())
            if not match:
                print(f"Invalid seat format: '{seat_str}'")
                return False

            row_num = int(match.group(1))
            col_num = match.group(2)
            print(f"DEBUG: Parsed seat - row: {row_num}, col: {col_num}")

            # שלב 2: קבלת פרטי המטוס והמחיר מהטיסה
            cursor.execute("SELECT plane_id, base_price FROM Flights WHERE flight_id = %s", (flight_id,))
            flight_data = cursor.fetchone()
            if not flight_data: 
                print(f"Flight {flight_id} not found")
                return False

            plane_id = flight_data[0]
            price = flight_data[1]
            print(f"DEBUG: Flight found - plane_id: {plane_id}, price: {price}")

            # שלב 3: בדיקה אם המושב תפוס (לפי שורה וטור בנפרד!)
            check_query = "SELECT * FROM Tickets WHERE flight_id=%s AND row_num=%s AND col_num=%s"
            cursor.execute(check_query, (flight_id, row_num, col_num))
            if cursor.fetchone():
                print(f"Seat {seat_str} is already taken")
                return False  # המושב תפוס

            # שלב 3.5: הוספת לקוח לטבלת Customers אם לא קיים (בגלל Foreign Key)
            customer_query = """
                INSERT IGNORE INTO Customers (customer_email, first_english_name, last_english_name)
                VALUES (%s, %s, %s)
            """
            cursor.execute(customer_query, (email, first_name, last_name))
            print(f"DEBUG: Customer created/exists: {email}")

            # שלב 4: יצירת הזמנה בטבלת Bookings
            booking_query = """
                INSERT INTO Bookings (customer_email, order_date, total_price, status)
                VALUES (%s, NOW(), %s, 'Active')
            """
            cursor.execute(booking_query, (email, price))
            order_id = cursor.lastrowid
            print(f"DEBUG: Created booking with order_id: {order_id}")

            # שלב 5: יצירת הכרטיס בטבלת Tickets
            ticket_query = """
                INSERT INTO Tickets (order_id, flight_id, plane_id, row_num, col_num, final_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(ticket_query, (order_id, flight_id, plane_id, row_num, col_num, price))
            ticket_id = cursor.lastrowid
            print(f"DEBUG: Created ticket with id: {ticket_id}")

            conn.commit()
            return ticket_id

        except Exception as e:
            print(f"Booking Error: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return False
        finally:
            if conn.is_connected(): cursor.close(); conn.close()