# third party access has been blocked for the email functionality
import json
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)
app = Flask(__name__)
db = firestore.client()


@app.route('/book', methods=['POST'])
def book_tutor():
    """This function books a tutor"""
    booking_records = request.get_json()
    query = db.collection('booking').where('booked_time', '==', booking_records['booked_time']).get()

    if len(query) > 0:
        return jsonify({'error': 'Time has already been booked.'}), 400

    # adding booking to the database
    db.collection('booking').document(booking_records['booking_id']).set(booking_records)

    student_name = booking_records['student_name']
    student_email = booking_records['student_email']
    tutor_name = booking_records['tutor_name']
    tutor_email = booking_records['tutor_email']
    course_name = booking_records['course_name']
    booked_time = booking_records['booked_time']

    send_tutor_notification(tutor_email, tutor_name, student_name,
                            student_email, course_name, booked_time)

    send_tutor_notification(student_email, student_name,
                            tutor_name, tutor_email,
                            course_name, booked_time)

    return jsonify({'message': 'Booking successful!'}), 201


@app.route('/book', methods=['DELETE'])
def cancel_booking():
    """This function cancels a booking"""
    record = json.loads(request.data)
    booking_id = record['booking_id']

    # Retrieving user record from Firestore
    booking_ref = db.collection('booking').document(booking_id)
    user_doc = booking_ref.get()

    if user_doc.exists:
        booking_ref.delete()

        return jsonify(''), 204

    else:
        return jsonify({'error': 'The data cannot be found'}), 404


def send_tutor_notification(tutor_email, tutor_name, student_name, student_email, course_name, booked_time):
    """This function notifies the tutor of a booking"""
    email_collection = db.collection('notifications').document()

    body = f'Hello {tutor_name}, \n\n {student_name} has booked ' \
           f'you for a tutoring session on {course_name} at {booked_time}. ' \
           f'Reach out to them at {student_email}'
    email = {
        "to": tutor_email,
        "message": {
            "subject": "New tutor booking",
            "html": body,
        }
    }
    email_collection.set(email)


def send_student_notification(student_email, student_name, tutor_name, tutor_email,
                              course_name, booked_time):
    """This email notifies the student of a successful booking"""
    notification_collection = db.collection('notifications').document()

    body = f'Hello {student_name}, \n\n You have booked {tutor_name} ' \
           f'for a tutoring session on {course_name} on {booked_time}. ' \
           f'Reach out to them at {tutor_email}. '

    notification = {
        "to": student_email,
        "message": {
            "subject": "New tutor booking",
            "html": body
        }
    }
    notification_collection.set(notification)


if __name__ == '__main__':
    app.run(debug=True)
