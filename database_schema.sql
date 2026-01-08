-- FLY_TAU Database Schema
-- Clean version without MySQL-specific comments

CREATE DATABASE IF NOT EXISTS FLY_TAU;
USE FLY_TAU;

-- =============================================
-- AIRPORTS
-- =============================================
CREATE TABLE Airports (
    airport_code VARCHAR(3) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    country VARCHAR(50) NOT NULL
);

-- =============================================
-- AIRPLANES
-- =============================================
CREATE TABLE Airplanes (
    plane_id INT PRIMARY KEY,
    manufacturer ENUM('Boeing', 'Airbus', 'Dassault') NOT NULL,
    size ENUM('Big', 'Small') NOT NULL,
    purchase_date DATE,
    num_of_seats INT
);

-- =============================================
-- SEATS
-- =============================================
CREATE TABLE Seats (
    plane_id INT NOT NULL,
    row_num INT NOT NULL,
    col_num CHAR(1) NOT NULL,
    class ENUM('Economy', 'Business') NOT NULL,
    PRIMARY KEY (plane_id, row_num, col_num),
    FOREIGN KEY (plane_id) REFERENCES Airplanes(plane_id) ON DELETE CASCADE
);

-- =============================================
-- ROUTES
-- =============================================
CREATE TABLE Routes (
    route_id INT PRIMARY KEY AUTO_INCREMENT,
    duration DECIMAL(10,2),
    origin_code VARCHAR(3) NOT NULL,
    dest_code VARCHAR(3) NOT NULL,
    FOREIGN KEY (origin_code) REFERENCES Airports(airport_code),
    FOREIGN KEY (dest_code) REFERENCES Airports(airport_code)
);

-- =============================================
-- EMPLOYEES
-- =============================================
CREATE TABLE Employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    street VARCHAR(100),
    city VARCHAR(50),
    apt_num INT,
    start_date DATE,
    phone_number VARCHAR(20)
);

-- =============================================
-- MANAGERS (inherits from Employees)
-- =============================================
CREATE TABLE Managers (
    employee_id INT PRIMARY KEY,
    manager_pass VARCHAR(255) NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE CASCADE
);

-- =============================================
-- PILOTS (inherits from Employees)
-- =============================================
CREATE TABLE Pilots (
    employee_id INT PRIMARY KEY,
    long_flight_certified BOOLEAN DEFAULT FALSE,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE CASCADE
);

-- =============================================
-- FLIGHT ATTENDANTS (inherits from Employees)
-- =============================================
CREATE TABLE Flight_Attendants (
    employee_id INT PRIMARY KEY,
    is_available BOOLEAN DEFAULT TRUE,
    long_flight_certified BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (employee_id) REFERENCES Employees(employee_id) ON DELETE CASCADE
);

-- =============================================
-- FLIGHTS
-- =============================================
CREATE TABLE Flights (
    flight_id INT PRIMARY KEY AUTO_INCREMENT,
    dep_time TIME NOT NULL,
    dep_date DATE NOT NULL,
    status ENUM('Scheduled', 'Full', 'Completed', 'Cancelled') DEFAULT 'Scheduled',
    base_price DECIMAL(10,2) NOT NULL,
    route_id INT NOT NULL,
    plane_id INT NOT NULL,
    manager_id INT,
    FOREIGN KEY (route_id) REFERENCES Routes(route_id),
    FOREIGN KEY (plane_id) REFERENCES Airplanes(plane_id),
    FOREIGN KEY (manager_id) REFERENCES Managers(employee_id)
);

-- =============================================
-- PILOT ASSIGNMENTS (Many-to-Many: Pilots <-> Flights)
-- =============================================
CREATE TABLE Pilot_Assignments (
    employee_id INT NOT NULL,
    flight_id INT NOT NULL,
    PRIMARY KEY (employee_id, flight_id),
    FOREIGN KEY (employee_id) REFERENCES Pilots(employee_id),
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE
);

-- =============================================
-- ATTENDANT ASSIGNMENTS (Many-to-Many: Attendants <-> Flights)
-- =============================================
CREATE TABLE Attendant_Assignments (
    employee_id INT NOT NULL,
    flight_id INT NOT NULL,
    PRIMARY KEY (employee_id, flight_id),
    FOREIGN KEY (employee_id) REFERENCES Flight_Attendants(employee_id),
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE
);

-- =============================================
-- CUSTOMERS
-- =============================================
CREATE TABLE Customers (
    customer_email VARCHAR(100) PRIMARY KEY,
    first_english_name VARCHAR(50),
    last_english_name VARCHAR(50)
);

-- =============================================
-- CUSTOMER PHONES (Multi-valued attribute)
-- =============================================
CREATE TABLE Customer_Phones (
    customer_email VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    PRIMARY KEY (customer_email, phone_number),
    FOREIGN KEY (customer_email) REFERENCES Customers(customer_email) ON DELETE CASCADE
);

-- =============================================
-- REGISTERED CUSTOMERS (inherits from Customers)
-- =============================================
CREATE TABLE Registered_Customers (
    customer_email VARCHAR(100) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    reg_date DATE DEFAULT (CURDATE()),
    birth_date DATE,
    pass_num VARCHAR(20),
    FOREIGN KEY (customer_email) REFERENCES Customers(customer_email) ON DELETE CASCADE
);

-- =============================================
-- GUEST CUSTOMERS (inherits from Customers)
-- =============================================
CREATE TABLE Guest_Customers (
    customer_email VARCHAR(100) PRIMARY KEY,
    FOREIGN KEY (customer_email) REFERENCES Customers(customer_email) ON DELETE CASCADE
);

-- =============================================
-- BOOKINGS (Orders)
-- =============================================
CREATE TABLE Bookings (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    order_date DATE DEFAULT (CURDATE()),
    total_price DECIMAL(10,2),
    status ENUM('Active', 'Completed', 'Cancelled_By_Customer', 'Cancelled_By_System') DEFAULT 'Active',
    customer_email VARCHAR(100) NOT NULL,
    FOREIGN KEY (customer_email) REFERENCES Customers(customer_email)
);

-- =============================================
-- TICKETS
-- =============================================
CREATE TABLE Tickets (
    ticket_id INT PRIMARY KEY AUTO_INCREMENT,
    final_price DECIMAL(10,2) NOT NULL,
    order_id INT NOT NULL,
    flight_id INT NOT NULL,
    plane_id INT NOT NULL,
    row_num INT NOT NULL,
    col_num CHAR(1) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES Bookings(order_id) ON DELETE CASCADE,
    FOREIGN KEY (flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY (plane_id, row_num, col_num) REFERENCES Seats(plane_id, row_num, col_num)
);
