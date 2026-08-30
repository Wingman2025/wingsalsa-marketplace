# Wingsalsa MarketPlace

## Product purpose

Wingsalsa MarketPlace helps visitors in Tarifa find a sports class and send a clear reservation request without creating an account. Jorge manages schools, activities, and requests from one private Django Admin.

## Primary journeys

1. Visitor discovers active activities and filters by sport or school.
2. Visitor reads one activity and sends a reservation request.
3. Visitor sees a clear confirmation that the request is not yet a confirmed booking.
4. Administrator creates schools and activities, reviews requests, and updates their status.

## Experience principles

- Mobile first, warm, energetic, and practical.
- One main action per public screen.
- Use short Spanish copy and distinguish a request from a confirmed reservation.
- Keep the MVP centralized: no customer accounts, school accounts, payments, or live availability.

## Critical visible states

- Catalog with results and without results.
- Activity available and inactive/not found.
- Booking form default, invalid, and successfully submitted.
- Admin authenticated and unauthenticated.

## Validation

- Run `python manage.py test`.
- Run `python manage.py check`.
- Review home, catalog, detail, form errors, and confirmation in a real browser at mobile and desktop widths.

