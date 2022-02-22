Using the API
----------------

Klub přatel provides a REST api using [django-rest-framework](https://www.django-rest-framework.org/). Django rest framework makes it easy to expose Django models to the outside world. Models are exposed using views that list objects. These lists use pagination.

There are also some views that do not correspond directly to models.

You can find swagger docs here:

[![Swagger docs](https://test.klub-pratel.cz/media/drf-yasg/swagger-ui-dist/favicon-32x32.40d4f2c38d1c.png) Swagger docs](https://test.klub-pratel.cz/api/docs/)

Also, if you open endpoints as Admin user in the browser you will be presented with a user friendly interface explaining how to use the endpoint.

Authentification
-------------------

In order to interact with the API you'll need authentification.

Klub přatel supports an OAuth flow for requesting an Access Token. [OAuth Application](https://test.klub-pratel.cz/oauth2_provider/application/add/).

You'll want to set the `Authorization grant type` to "Client credentials".

Furthermore, if you want your application to have access to event data you need to add the `can_view_events` scope to the scope string.
 
To test your new application you can request a token using the curl command
 
 ```
curl --header "Content-Type: application/json" --request POST --data '{"grant_type":"client_credentials","client_id":"<id>","client_secret":"<secret>"}' https://test.klub-pratel.cz/api/o/token
 ```
 
 You can then use your token like so:
 
 ```
curl -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -X GET https://test.klub-pratel.cz/api/bronto/event/
 ```
 
Registering users via API
------------------------------

The endpoint for registering users is `/api/register-userprofile`. Here are some example contents:

```
{
    "username": "test2",
    "password": "foobarbaz",
    "first_name": "Test",
    "last_name": "Test",
    "telephone": "334534534",
    "email": "test@example.com",
    "userchannels": [
      {
        "money_account": "obecne_darujme",
        "event": "obecne",
        "regular_amount": 250,
        "regular_frequency": "monthly"
        
      }
    ]
}
```

Possible values for `regular_frequency` are

- `monthly`
- `quaterly`
- `biannually`
- `annually`

`money_account` and `event ` should be set to slugs.

You can find event slugs in the admin at `/events/event/` for example `https://test.klub-pratel.cz/events/event/`.

Money account slugs are in the admin at `/aklub/bankaccount/` aka `https://test.klub-pratel.cz/aklub/bankaccount/`


Please note this endpoint is likely to be updated in the future to include a CAPTCHA code.

Resetting passwords
-----------------------

Password reset emails can be triggered with the `reset_password_email/` endpoint. This endpoint takes a json object with a single field `email`:

Example

```
{
   "email": "foo@example.com"
}
```

Please note this endpoint is likely to be updated in the future to include a CAPTCHA code.

 
User based Login Flows
---------------------------

You can log in to the user based rest API using the endpoint `http://localhost:8000/api/token/`. This will give you a JWT token.

You can get your refresh token using the endpoint `http://localhost:8000/api/token/refresh/`

You can then send request using the usage [can be found inthe simplejwt docs](https://django-rest-framework-simplejwt.readthedocs.io/en/latest/getting_started.html#usage).

Finding out about the current user
-----------------------------------------

There are various levels of permissions that users can have in the front end:

0. Anonymous User
 - Can see the structure of the organization: Administrative Units
 - Can view all events
1. Ordinary user:
 - Can find out which events they signed up: `https://test.klub-pratel.cz/api/frontend/my_events/`
 - Can update events that they have organized: `https://test.klub-pratel.cz/api/frontend/organized_events/`
 - Can list their own interactions: TODO
 - Can express interest in an event:  `https://test.klub-pratel.cz/api/frontend/my_events/`
2. Event organizers and Staff: TODO
 - Can create update Events in their Administrative Units
 - Can update events organizational team: TODO
 - Can search for users by name/email: `https://test.klub-pratel.cz/api/frontend/users/?q=<username>`
 - Can see which users are registered for an event and mark attendance: `https://test.klub-pratel.cz/api/frontend/attendees/`
3. Superusers
 - Can create and update events globally
 - Access all other endpoints: see the [Swagger docs](https://test.klub-pratel.cz/api/docs/)
 
 
Who am I?
-----------

Once you are logged in you can find out what kind of user you are with the

`api/frontend/whoami`

endpoint. With this endpoint, you can also update your own First and Last name.

Administrative Units
-------------------------

Administrative units can be viewed at the endpoint `/api/bronto/administrative_unit/`

Open globally

Payments
----------

Users can check if their payment is up to date according to their subscription using the `check_last_payment/` endpoint which returns 200 if up to date and 404 otherwise.


Events
-------

The endpoint `https://test.klub-pratel.cz/api/bronto/event/` lists all events.

**Creating editing events**:

- Event organizers, Admins

- permissions GET, POST

- endpoint `https://test.klub-pratel.cz/api/frontend/events/`

**Editing events (direct organizers)**

You can see and update events you are organizing at the endpoint

`https://test.klub-pratel.cz/api/frontend/organized_events/`

**Signing up for events (normal users)**

Users can sign up to see the events they have signed up for and sign up for new ones by visiting the endpoint:

`http://localhost:8000/api/frontend/my_events/`

Note: Answers to additional questions should be put into the field `summary`.

The field `type__slug`, refers to an interaction type which must be manually configured in the admin at the URL:

`http://localhost:8000/interactions/interactiontype/`

**Seeing who's registered for an event and taking attendance**

 - Admin/event organizers only
 - Endpoint `https://test.klub-pratel.cz/api/frontend/attendees/`
 - `type__slug` options: ["`event_registration`", "`event_attendance`"]


Event Types
-------------

- Admins, Event organizers

- permissions GET

- endpoint `https://test.klub-pratel.cz/api/frontend/event-type/`


Locations
-------

- Admin, Event organizers only

- permissions GET, POST, DELETE

- endpoint `https://test.klub-pratel.cz/api/frontend/location/`


Searching for Users
-----------------------

- Admin, event organizers only

- permissions GET

- endpoint `https://test.klub-pratel.cz/api/frontend/users/?q=<username>`

The `q` query param is optional.

You can get a user by ID with urls of the form:

`https://test.klub-pratel.cz/api/frontend/users/<id>/`

Editing userprofiles
--------------------------

- Admin, event organizers only

- permissions GET, PATCH

- endpoint

- endpoint `https://test.klub-pratel.cz/api/frontend/edit_userprofile/<id>/?dob=<YYYY-MM-DD>`

Allows you to edit user profiles. Note: You must specify the users date of birth by passing the `dob` query arg in the format `YYYY-MM-DD`.

"Unknown" user endpoints: Get or create user profile
-------------------------------------------------------------------

The following endpoints will add an intraction to an existing user profile or or create a new one.

They all share the following fields:

 - `first_name`
 - `last_name`
 - `telephone`
 - `email`: required
 - `note`
 - `age_group`
 - `birth_month`
 - `birth_day`
 - `street`
 - `city`
 - `zip_code`

These endpoints identify users by email. They will only update fields that aren't already set in the DB. Notes will be appended together.

Returns `user_id` of the gotten or created user.

Signing up "unknown" users for events
-----------------------------------------------

 - Endpoint `/api/sign_up_for_event`

 - Takes typical fields for creating a user profile as well as:
    
    - `event`
    - `skills`: A string, which should be a list of skill hashtags like `"#cooking #html5"`
    - `additional_question_1`: Answers to the additional questions attached to the event. Will be stored to the interaction summary.
    - `additional_question_2`
    - `additional_question_3`
    - `additional_question_4`


Signing up "unknown" users as volunteers
-----------------------------------------------

 - Endpoint `/api/volunteer`
 - Additional fields
   - `administrative_unit`: PK of administrative unit the person is applying to volunteer for
   - `skills`: Hashtag list of skills the person has
   - `event`: Optional event the user is volunteering for
   - `summary`: Any text the user might add to their offer
   - `location`: Optional pk of location the user is interested in helping with
   - `program_of_interest`: List of `ORGANIZATION_FINANCE_PROGRAM_TYPES` the user is interested in helping with.
 

Applying "unknown" users for membership
-----------------------------------------------

 - Endpoint `/api/apply_for_membership`
 - Additional fields
  - `administrative_unit`
  - `skills`
