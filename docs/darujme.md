Setting up Darujme
=======================


Adding an API account
-------------------------

In order to connect with Darujme you need to add an API access point which you can do in the admin at the address: https://test.klub-pratel.cz/aklub/apiaccount/

Once an access point has been configured you can press "Save and Contnue". At the bottom of the page you should now see a field "Daruje API url" which has been filled in with a "Here" button. If you press on the "Here" button you should see a list of Darujme pledges. If this list is empty, either there have been no pledges, or you've filled out your credentials wrong.

Adding a Periodic Task
---------------------------

After you do this, you should set up a periodic task for Darujme by adding one here https://test.klub-pratel.cz/django_celery_beat/periodictask/

You should set the `Task (custom)` field to `aklub.tasks.check_darujme` .
You can ten set the interval using the `Crontab Schedule` field. To learn how to write Crontab intervals use the [crontab guru site](https://crontab.guru/).

Once you have saved and enabled your task, Klub Přatel will automatically sync your Darujme pledges.

Happy fundraising!
