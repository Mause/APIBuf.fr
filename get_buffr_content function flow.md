# `get_buffr_content` function flow

This is to help me understand the function flow.
It seems surprisingly complicated.

is passed;

     - dictionary containing;
        - Buffr Model
        - last time cached data was updated
     - relative url, determined by regex
     - handler object, to change http status

1. Checks if lasttime difference is greater than the update_interval attribute on the Buffr Model.
2. If it is, note that the users api is going to have to be fetched from.
3. If not, serve last_known_data attribute from Buffr Model
