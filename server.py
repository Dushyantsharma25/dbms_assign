# To run this file type python server.py
# To see website type http://localhost:8000/


from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from pymongo import MongoClient
from bson.objectid import ObjectId  

client = MongoClient("mongodb://localhost:27017")
db = client["mydatabase"]
collection = db["customers"]

class RestaurantHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html>
            <head><title>Restaurant Order Form</title></head>
            <body>
                <h2>Place Your Order</h2>
                <form action="/submit" method="POST">
                    Name: <input type="text" name="name" required><br><br>
                    Order: <input type="text" name="order" required><br><br>
                    Price: <input type="number" step="0.01" name="price" required><br><br>
                    Phone Number: <input type="tel" name="phone" required><br><br>
                    <input type="submit" value="Submit Order">
                </form>
                <br>
                <a href="/orders">View All Orders</a>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif path == "/orders":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = """
            <html>
            <body>
                <h2>All Orders</h2>
                <table border="1">
                    <tr><th>Name</th><th>Order</th><th>Price</th><th>Phone</th><th>Actions</th></tr>
            """

            for order in collection.find():
                html += f"""
                <tr>
                    <td>{order['name']}</td>
                    <td>{order['order']}</td>
                    <td>{order['price']:.2f}</td>
                    <td>{order['phone']}</td>
                    <td>
                        <a href="/edit?id={order['_id']}">Edit</a> |
                        <a href="/delete?id={order['_id']}">Delete</a>
                    </td>
                </tr>
                """
            html += "</table><br><a href='/'>Back to Order Form</a></body></html>"
            self.wfile.write(html.encode())

        elif path == "/delete":
            order_id = query.get("id", [""])[0]
            try:
                collection.delete_one({"_id": ObjectId(order_id)})
            except:
                pass  
            self.send_response(302)
            self.send_header("Location", "/orders")
            self.end_headers()

        elif path == "/edit":
            order_id = query.get("id", [""])[0]
            order = collection.find_one({"_id": ObjectId(order_id)})

            if order:
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                html = f"""
                <html>
                <body>
                    <h2>Edit Order</h2>
                    <form action="/edit" method="POST">
                        <input type="hidden" name="id" value="{order_id}">
                        Name: <input type="text" name="name" value="{order['name']}" required><br><br>
                        Order: <input type="text" name="order" value="{order['order']}" required><br><br>
                        Price: <input type="number" step="0.01" name="price" value="{order['price']}" required><br><br>
                        Phone: <input type="tel" name="phone" value="{order['phone']}" required><br><br>
                        <input type="submit" value="Update Order">
                    </form>
                    <br><a href="/orders">Cancel</a>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"<h2>Order not found</h2>")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        data = parse_qs(post_data)

        if path == "/submit":
            name = data.get("name", [""])[0]
            order = data.get("order", [""])[0]
            price = data.get("price", [""])[0]
            phone = data.get("phone", [""])[0]

            if name and order and price and phone:
                try:
                    price_float = float(price)
                except ValueError:
                    price_float = 0.0

                collection.insert_one({
                    "name": name,
                    "order": order,
                    "price": price_float,
                    "phone": phone
                })

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                response = f"""
                <html>
                <body>
                    <h2>Thanks, {name}!</h2>
                    <p>Your order for '{order}' at {price_float:.2f} rs has been received.</p>
                    <p>We will contact you shortly at {phone}.</p>
                    <a href="/">Place another order</a> | <a href="/orders">View Orders</a>
                </body>
                </html>
                """
                self.wfile.write(response.encode())
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"<html><body><h2>Error: Missing fields!</h2><a href='/'>Try again</a></body></html>")

        elif path == "/edit":
            order_id = data.get("id", [""])[0]
            name = data.get("name", [""])[0]
            order = data.get("order", [""])[0]
            price = data.get("price", [""])[0]
            phone = data.get("phone", [""])[0]

            if order_id and name and order and price and phone:
                try:
                    price_float = float(price)
                    collection.update_one(
                        {"_id": ObjectId(order_id)},
                        {"$set": {
                            "name": name,
                            "order": order,
                            "price": price_float,
                            "phone": phone
                        }}
                    )
                except:
                    pass

            self.send_response(302)
            self.send_header("Location", "/orders")
            self.end_headers()


def run():
    print("Starting server at http://localhost:8000")
    server = HTTPServer(('localhost', 8000), RestaurantHandler)
    server.serve_forever()

if __name__ == "__main__":
    run()

