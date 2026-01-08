# ZMJ (Zažít město jinak) Documentation

Deployed app [here](https://klub-zmj-test.dopracenakole.net/)

## Overview

ZMJ (Zažít město jinak) is a program module in the Klub system that allows users to register and manage events. It provides a REST API for event organizers to:

- Register and manage their user profiles
- Create and manage events
- Handle event content, organizers, companies, and programs
- Manage agreements, invoices, and checklists

Additionally, ZMJ provides public endpoints that allow anyone to view information about events that are marked as public on the web, without requiring authentication.

## Development Setup

### Prerequisites

- Docker and Docker Compose installed
- Git repository cloned

### Initial Setup

1. **Copy environment file:**
   ```bash
   cp .env-zmj .env
   ```

2. **Build and start Docker containers:**
   ```bash
   docker compose build --build-arg UID=$UID
   docker compose up
   ```

3. **In new terminal run**
   ```bash
   docker exec -it klub-web-1 bash
   python manage.py migrate
   python manage.py createsuperuser2 --profile=user --username="superuser"
   ```

### Starting the Development Server

**Start the development environment:**
   ```bash
   docker exec -it klub-web-1 bash
   python manage.py runserver 0.0.0.0:8000
   ```

### ZMJ-Specific Configuration

For ZMJ development, you can use the `.env-zmj` file as a reference. The key settings include:

- `DJANGO_SETTINGS_MODULE`: Set to appropriate settings module (e.g., `project.settings.ced_dev_local`)

### Add data before

You can (and should) add data before run FE app.
```
docker exec -it klub-web-1 bash
python manage.py load_categories
python manage.py load_company_types
```

## Source Code Structure

The ZMJ module is located in `apps/api/zmj/`:

```
apps/api/zmj/
├── urls.py              # URL routing configuration
├── views.py             # API view classes
└── serializers.py       # Data serialization/validation
```

### Key Components

#### Views (`apps/api/zmj/views.py`)
- **UserProfileView**: Get and update user profile information
- **RegistrationView**: Register new users and create events
- **RegistrationStatusView**: Check registration completion status
- **CompanyTypesView**: List available company types
- **CategoriesView**: List available event categories
- **UserEventsView**: List events organized by the user
- **EventDetailView**: Get and update event details
- **EventContentView**: Manage event content (photos, descriptions, URLs)
- **EventPublicOnWebView**: Check if event is public on web
- **CompanyView**: Manage company information for events
- **EventOrganizersView**: Manage event organizers
- **EventProgramsView**: Manage event programs (child events)
- **EventProgramDetailView**: Get, update, or delete specific programs
- **EventAgreementView**: Manage event agreements and signed PDFs
- **EventInvoiceView**: Get invoice status and files
- **EventChecklistView**: Manage event checklist items
- **EventChecklistItemView**: Update individual checklist items
- **PublicEventListView**: List all public events (no authentication required)
- **PublicEventDetailView**: Get detailed information about a public event (no authentication required)

#### Serializers (`apps/api/zmj/serializers.py`)
- **UpdateUserProfileSerializer**: User profile updates
- **RegistrationSerializer**: Complete registration with event creation
- **UpdateEventSerializer**: Event information updates
- **CompanySerializer**: Company profile management
- **EventContentSerializer**: Event content fields
- **OrganizerSerializer**: Organizer contact information
- **EventProgramSerializer**: Event program (child event) management
- **AgreementStatusSerializer**: Agreement status and PDF files
- **AgreementSignedUploadSerializer**: Upload signed agreement PDFs
- **InvoiceStatusSerializer**: Invoice status and PDF files
- **EventChecklistItemSerializer**: Checklist item management
- **PublicEventListSerializer**: Public event list with basic information
- **PublicEventDetailSerializer**: Public event detail with full information

### Administrative Units

ZMJ uses the `AdministrativeUnit` model to organize users and events. When a user registers or updates their profile without an administrative unit, they are automatically assigned to the "ZMJ" administrative unit.

## API Endpoints

All endpoints are prefixed with `/api/zmj/`. Most endpoints require authentication (`IsAuthenticated` permission), except for the public endpoints which are accessible without authentication (`AllowAny` permission).

### User Profile

#### GET `/api/zmj/user/`
Get authenticated user's profile information.

**Response:**
```json
{
  "firstname": "John",
  "lastname": "Doe",
  "email": "john@example.com",
  "telephone": "+420123456789",
  "sex": "M",
  "language": "cs",
  "send_mailing_lists": true,
  "newsletter_on": false
}
```

#### PUT/PATCH `/api/zmj/user/`
Update user profile information.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "telephone": "+420123456789",
  "sex": "M",
  "language": "cs",
  "send_mailing_lists": true,
  "newsletter_on": false
}
```

### Registration

#### POST `/api/zmj/registration/`
Register a new user and create an event. This endpoint creates:
- User profile with contact information
- Event with location
- Organization team link
- Agreement and Invoice (draft status)
- Predefined checklist items
- Optional company profile
- Optional additional organizers

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "telephone": "+420123456789",
  "sex": "M",
  "send_mailing_lists": true,
  "newsletter_on": false,
  "event_name": "My Event",
  "event_date": "2024-06-15T10:00:00Z",
  "gps_latitude": 50.0755,
  "gps_longitude": 14.4378,
  "place": "Prague",
  "space_type": "public",
  "space_area": "100m²",
  "space_rent": false,
  "activities": "Workshop, Music",
  "company_name": "My Company",
  "company_type_id": 1,
  "company_crn": "12345678",
  "company_tin": "CZ12345678",
  "organizers": [
    {
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane@example.com",
      "telephone": "+420987654321"
    }
  ]
}
```

#### GET `/api/zmj/registration/status/`
Check if user registration is complete.

**Response:**
```json
{
  "is_complete": true
}
```

Checks:
- `first_name` is filled
- `last_name` is filled
- `telephone` is filled
- User has an event with a name

### Reference Data

#### GET `/api/zmj/company-types/`
Get all available company types.

**Response:**
```json
[
  {"id": 1, "type": "s.r.o."},
  {"id": 2, "type": "a.s."}
]
```

#### GET `/api/zmj/categories/`
Get all available event categories.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Workshop",
    "slug": "workshop",
    "description": "Educational workshop"
  }
]
```

### Events

#### GET `/api/zmj/events/`
List all events organized by the authenticated user.

**Response:**
```json
[
  {
    "id": 1,
    "slug": "my-event",
    "name": "My Event"
  }
]
```

#### GET `/api/zmj/events/<event_slug>/`
Get event details.

**Response:**
```json
{
  "name": "My Event",
  "date": "2024-06-15T10:00:00Z",
  "place": "Prague",
  "latitude": 50.0755,
  "longitude": 14.4378,
  "space_area": "100m²",
  "space_type": "public",
  "space_rent": false,
  "activities": "Workshop, Music"
}
```

#### PUT `/api/zmj/events/<event_slug>/`
Update event information.

**Request Body:**
```json
{
  "name": "Updated Event Name",
  "date": "2024-06-20T10:00:00Z",
  "place": "Brno",
  "latitude": 49.1951,
  "longitude": 16.6068
}
```

### Event Content

#### GET `/api/zmj/events/<event_slug>/content/`
Get event content.

**Response:**
```json
{
  "main_photo": "https://example.com/media/photos/event.jpg",
  "description": "Event description",
  "url": "https://example.com",
  "url_title": "Website",
  "url1": "https://facebook.com/event",
  "url_title1": "Facebook",
  "url2": "https://instagram.com/event",
  "url_title2": "Instagram"
}
```

#### PUT `/api/zmj/events/<event_slug>/content/`
Update event content.

**Request Body:**
```json
{
  "main_photo": "<file>",
  "description": "Updated description",
  "url": "https://example.com",
  "url_title": "Website",
  "url1": "https://facebook.com/event",
  "url_title1": "Facebook",
  "url2": "https://instagram.com/event",
  "url_title2": "Instagram"
}
```

#### GET `/api/zmj/events/<event_slug>/public-on-web/`
Check if event is public on web.

**Response:**
```json
{
  "public_on_web": true
}
```

### Company

#### GET `/api/zmj/events/<event_slug>/company/`
Get company information for the event (returns `null` if no company).

**Response:**
```json
{
  "name": "My Company",
  "company_type": 1,
  "company_type_name": "s.r.o.",
  "crn": "12345678",
  "tin": "CZ12345678"
}
```

#### PUT `/api/zmj/events/<event_slug>/company/`
Create or update company information.

**Request Body:**
```json
{
  "name": "My Company",
  "company_type": 1,
  "crn": "12345678",
  "tin": "CZ12345678"
}
```

### Organizers

#### GET `/api/zmj/events/<event_slug>/organizers/`
List all organizers for the event (excluding authenticated user).

**Response:**
```json
[
  {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "telephone": "+420987654321"
  }
]
```

#### PUT `/api/zmj/events/<event_slug>/organizers/`
Replace the list of organizers (list replacement pattern).

**Request Body:**
```json
[
  {
    "id": 2,
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane@example.com",
    "telephone": "+420987654321"
  },
  {
    "first_name": "Bob",
    "last_name": "Johnson",
    "email": "bob@example.com",
    "telephone": "+420111222333"
  }
]
```

- Items with `id` are updated
- Items without `id` are created
- Organizers not in the list are removed from the event (except authenticated user)

### Programs (Child Events)

#### GET `/api/zmj/events/<event_slug>/program/`
List all programs (child events) for the event.

**Response:**
```json
[
  {
    "id": 1,
    "name": "Morning Workshop",
    "description": "Workshop description",
    "time_from": "2024-06-15T09:00:00Z",
    "time_to": "2024-06-15T12:00:00Z",
    "categories": [
      {"id": 1, "name": "Workshop", "slug": "workshop"}
    ]
  }
]
```

#### POST `/api/zmj/events/<event_slug>/program/`
Create a new program.

**Request Body:**
```json
{
  "name": "Morning Workshop",
  "description": "Workshop description",
  "time_from": "2024-06-15T09:00:00Z",
  "time_to": "2024-06-15T12:00:00Z",
  "categories": [1, 2]
}
```

#### GET `/api/zmj/events/<event_slug>/program/<program_id>/`
Get program details.

#### PUT/PATCH `/api/zmj/events/<event_slug>/program/<program_id>/`
Update program.

#### DELETE `/api/zmj/events/<event_slug>/program/<program_id>/`
Delete program.

### Agreement

#### GET `/api/zmj/events/<event_slug>/agreement/`
Get agreement status and conditional PDF files.

**Response:**
```json
{
  "status": "sent",
  "pdf_file": "https://example.com/media/agreements/agreement.pdf",
  "pdf_file_completed": null
}
```

- `status`: Always returned
- `pdf_file`: Returned if status is "sent" or "rejected"
- `pdf_file_completed`: Returned if status is "completed"

#### POST `/api/zmj/events/<event_slug>/agreement/`
Upload signed agreement PDF (only allowed when status is "sent" or "rejected").

**Request Body:**
```json
{
  "pdf_file_signed": "<file>"
}
```

### Invoice

#### GET `/api/zmj/events/<event_slug>/invoice/`
Get invoice status and conditional PDF file.

**Response:**
```json
{
  "status": "sent",
  "pdf_file": "https://example.com/media/invoices/invoice.pdf"
}
```

- `status`: Always returned
- `pdf_file`: Returned if status is "sent", "reminded", or "overdue"

### Checklist

#### GET `/api/zmj/events/<event_slug>/checklist/`
Get checklist items (predefined and custom).

**Response:**
```json
{
  "predefined": [
    {
      "id": 1,
      "name": "Draw a map of the area",
      "checked": false,
      "custom": false
    }
  ],
  "custom": [
    {
      "id": 2,
      "name": "Custom task",
      "checked": true,
      "custom": true
    }
  ]
}
```

#### PUT `/api/zmj/events/<event_slug>/checklist/`
Replace the list of custom checklist items.

**Request Body:**
```json
[
  {
    "id": 2,
    "name": "Updated custom task",
    "checked": true,
    "custom": true
  },
  {
    "name": "New custom task",
    "checked": false,
    "custom": true
  }
]
```

- Items with `id` are updated
- Items without `id` are created
- Custom items not in the list are deleted

#### PATCH `/api/zmj/events/<event_slug>/checklist/<item_id>/`
Update the checked status of a checklist item.

**Request Body:**
```json
{
  "checked": true
}
```

## Public Endpoints

The following endpoints are publicly accessible and do not require authentication. They provide read-only access to events that are marked as public on the web (`public_on_web=True`).

### Public Events List

#### GET `/api/zmj/public/events/`
Get a list of all public events. Returns basic information for each event.

**Authentication:** Not required (`AllowAny`)

**Response:**
```json
[
  {
    "name": "My Public Event",
    "slug": "my-public-event",
    "date": "2024-06-15T10:00:00Z",
    "location_place": "Prague"
  },
  {
    "name": "Another Event",
    "slug": "another-event",
    "date": "2024-06-20T14:00:00Z",
    "location_place": "Brno"
  }
]
```

**Response Fields:**
- `name`: Event name
- `slug`: Event slug (used for detail endpoint)
- `date`: Event start date/time (ISO 8601 format)
- `location_place`: Location place name (or `null` if no location)

**Notes:**
- Only events with `public_on_web=True` are returned
- Events are ordered by start date (most recent first)
- Events without a location will have `location_place: null`

### Public Event Detail

#### GET `/api/zmj/public/events/<event_slug>/`
Get detailed information about a specific public event.

**Authentication:** Not required (`AllowAny`)

**Response:**
```json
{
  "name": "My Public Event",
  "date": "2024-06-15T10:00:00Z",
  "main_image": "https://example.com/media/photos/event.jpg",
  "description": "A wonderful public event description",
  "links": [
    {
      "url": "https://example.com/event",
      "url_title": "Event Website"
    },
    {
      "url": "https://facebook.com/event",
      "url_title": "Facebook Page"
    }
  ],
  "location": {
    "place": "Prague",
    "gps_latitude": 50.0755,
    "gps_longitude": 14.4378
  },
  "organizer": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com"
  },
  "program_items": [
    {
      "name": "Morning Workshop",
      "description": "Educational workshop in the morning",
      "time_from": "2024-06-15T09:00:00Z",
      "time_to": "2024-06-15T12:00:00Z",
      "categories": [
        {
          "id": 1,
          "name": "Workshop",
          "slug": "workshop"
        }
      ]
    },
    {
      "name": "Afternoon Concert",
      "description": "Live music performance",
      "time_from": "2024-06-15T14:00:00Z",
      "time_to": "2024-06-15T17:00:00Z",
      "categories": [
        {
          "id": 2,
          "name": "Music",
          "slug": "music"
        }
      ]
    }
  ]
}
```

**Response Fields:**
- `name`: Event name
- `date`: Event start date/time (ISO 8601 format)
- `main_image`: URL to the main event photo (or `null` if not set)
- `description`: Event description (may be empty string)
- `links`: Array of link objects with `url` and `url_title` (up to 3 links: `url`/`url_title`, `url1`/`url_title1`, `url2`/`url_title2`)
- `location`: Location object with:
  - `place`: Location place name (or `null`)
  - `gps_latitude`: GPS latitude (or `null`)
  - `gps_longitude`: GPS longitude (or `null`)
- `organizer`: Organizer information with:
  - `first_name`: Organizer's first name (or `null`)
  - `last_name`: Organizer's last name (or `null`)
  - `email`: Organizer's primary email (or `null`)
- `program_items`: Array of program items (child events) with:
  - `name`: Program item name
  - `description`: Program item description (may be empty string)
  - `time_from`: Program start time (ISO 8601 format, or `null`)
  - `time_to`: Program end time (ISO 8601 format, or `null`)
  - `categories`: Array of category objects with `id`, `name`, and `slug`

**Error Responses:**

**404 Not Found:**
```json
{
  "error": "Event not found or not public."
}
```

This error is returned when:
- The event slug doesn't exist
- The event exists but `public_on_web=False`

**Notes:**
- Only events with `public_on_web=True` are accessible
- The organizer information is taken from the first `UserProfile` organizer linked to the event
- Program items are ordered by start time (`time_from`)
- Links are only included if both `url` and `url_title` are set (empty links are excluded)
- If no organizer is found, all organizer fields will be `null`

## Key Features

### Automatic Administrative Unit Assignment

When a user registers or updates their profile without an administrative unit, they are automatically assigned to the "ZMJ" administrative unit:

```python
if not user.administrative_units.exists():
    zmj_admin_unit, _created = AdministrativeUnit.objects.get_or_create(
        name="ZMJ",
        defaults={'level': 'club'}
    )
    user.administrative_units.add(zmj_admin_unit)
```

### Event Creation Flow

When a user registers via `/api/zmj/registration/`, the system:

1. Creates/updates user profile
2. Assigns ZMJ administrative unit if needed
3. Creates event with location
4. Links user as organizer via `OrganizationTeam`
5. Creates draft `Agreement` and `Invoice`
6. Creates predefined checklist items:
   - Draw a map of the area
   - Arrange signs
   - Print press materials
   - Arrange a partnership
   - Invite local institutions
   - Prepare the program
7. Optionally creates company profile
8. Optionally creates additional organizers

### Access Control

All endpoints use the `EventAccessMixin` to ensure users can only access events they organize. The mixin checks if the user is linked to the event via `OrganizationTeam`.

### Preferences Management

User preferences (`send_mailing_lists`, `newsletter_on`) are stored in the `Preference` model, which requires an administrative unit. Preferences are saved per administrative unit, allowing users to have different settings for different units.

## Configuration

ZMJ is configured in `project/settings/base.py`:

- Installed app: `"zmj"`
- Program name: `("zmj", "Zažít město jinak")`

## Related Documentation

- [API Documentation](./API.md) - General API documentation

<img src="https://fit.cvut.cz/static/images/fit-cvut-logo-en.svg" alt="FIT CTU logo" height="200">

This software was developed with the support of the **Faculty of Information Technology, Czech Technical University in Prague**.
For more information, visit [fit.cvut.cz](https://fit.cvut.cz).