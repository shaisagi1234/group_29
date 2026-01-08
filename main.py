from flask import Flask, render_template, request, redirect, url_for
from db_access import DbManager
from datetime import date

app = Flask(__name__)
db_manager = DbManager()


@app.route('/')
def home_page():
    airports = db_manager.get_all_airports()
    today = date.today().strftime('%Y-%m-%d')
    return render_template('home_page.html', airports=airports, today=today)


@app.route('/search-results', methods=['POST'])
def search_results():
    origin_raw = request.form.get('origin')
    dest_raw = request.form.get('destination')
    date = request.form.get('departure_date')
    passengers = int(request.form.get('passengers'))

    origin_city = origin_raw.split(' (')[0] if '(' in origin_raw else origin_raw
    dest_city = dest_raw.split(' (')[0] if '(' in dest_raw else dest_raw

    flights = db_manager.search_flights(origin_city, dest_city, date, passengers)

    return render_template('search_results.html',
                           flights=flights,
                           origin=origin_city,
                           dest=dest_city,
                           date=date,
                           passengers=passengers)


@app.route('/my_bookings', methods=['GET', 'POST'])
def my_bookings():
    booking_result = None
    error_msg = None
    if request.method == 'POST':
        email = request.form.get('email')
        order_id = request.form.get('order_id')
        booking_result = db_manager.get_ticket_details(email, order_id)
        if not booking_result:
            error_msg = "No booking found with these details."
    return render_template('my_bookings.html', booking=booking_result, error=error_msg)


@app.route('/booking', methods=['GET', 'POST'])
def booking_page():
    flight_id = request.args.get('flight_id')
    passengers = int(request.args.get('passengers', 1))
    if not flight_id: return "Error: No flight ID"

    flight, taken_seats, all_seats = db_manager.get_flight_seats(flight_id)
    if not flight: return "Error: Flight not found or DB error"

    return render_template('booking.html', flight=flight, taken_seats=taken_seats, all_seats=all_seats, passengers=passengers)


@app.route('/confirm-booking', methods=['POST'])
def confirm_booking():
    flight_id = request.form.get('flight_id')
    seat = request.form.get('selected_seat')
    email = request.form.get('email')
    name = request.form.get('passenger_name')

    ticket_id = db_manager.add_ticket(flight_id, seat, email, name)

    if ticket_id:
        return render_template('booking_confirmation.html',
                               ticket_id=ticket_id, flight_id=flight_id, seat=seat, email=email)
    else:
        return "Error: Seat already taken or DB error."


@app.route('/passenger_details', methods=['POST'])
def passenger_details():
    flight_id = request.form.get('flight_id')
    seats = request.form.getlist('seats')  # קבלת רשימה של מושבים
    price = request.form.get('price', 0)
    passengers = int(request.form.get('passengers', 1))
    
    return render_template('passenger_details.html', 
                          flight_id=flight_id, 
                          seats=seats, 
                          price=price,
                          passengers=passengers)


@app.route('/finalize_booking', methods=['POST'])
def finalize_booking():
    flight_id = request.form.get('flight_id')
    seats = request.form.get('seats', '').split(',')
    price = request.form.get('price')
    passengers = int(request.form.get('passengers', 1))
    
    # פרטי נוסע אחד לכל המושבים
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    
    print(f"DEBUG finalize_booking: flight_id={flight_id}, seats={seats}, email={email}, first_name={first_name}, last_name={last_name}")
    
    if not first_name or not last_name or not email or not seats:
        return "Error: Missing required information."
    
    # יצירת כרטיס לכל מושב
    all_tickets = []
    for seat in seats:
        seat = seat.strip()
        print(f"DEBUG: Processing seat '{seat}'")
        if seat:
            ticket_id = db_manager.add_ticket(flight_id, seat, email, first_name, last_name)
            print(f"DEBUG: add_ticket returned: {ticket_id}")
            if ticket_id:
                all_tickets.append(ticket_id)
    
    if all_tickets:
        return render_template('booking_confirmation.html',
                             order_id=all_tickets[0],
                             email=email,
                             seats=seats,
                             passengers=len(all_tickets))
    else:
        return "Error: Could not complete booking. Some seats may already be taken."


@app.route('/login')
def login(): return render_template('login.html')


@app.route('/register')
def register(): return render_template('register.html')


@app.route('/admin')
def admin_dashboard(): return render_template('admin_dashboard.html')


if __name__ == '__main__':
    app.run(debug=True)