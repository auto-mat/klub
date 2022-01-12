Tax Deduction PDFs
----------------------

In order to create tax confirmations you'ľl need to set up [smmapdfs](https://github.com/auto-mat/smmapdfs).

1. upload a ttf font to `http://localhost:8000/smmapdfs/pdfsandwichfont/`

2. add a template PDF to `http://localhost:8000/smmapdfs/pdfsandwichtype/`. After saving using "save and continue" you should be able to configure "Tax confirmation fields" to overlay text onto your tax confirmation.

3. You should add an email template for each language and connect it with your pdf template `http://localhost:8000/smmapdfs/pdfsandwichemail/`

4. In the user profiles admin `http://localhost:8000/aklub/userprofile/` you can use the admin action "Create tax confirmation"

5. This will create tax confirmation objects which you can view here `http://localhost:8000/aklub/taxconfirmation/`. You may need to run the `Make PDF sandwich` command on the tax confirmations, but the PDFs should be generated automatically and this shouldn't be necessary.

6. Go to the `http://localhost:8000/aklub/taxconfirmationpdf/` admin and use the `Send PDF sandwich` command to send the tax confirmations via email.
