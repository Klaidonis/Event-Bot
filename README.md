![Header](assets/Event-bot.png)

## A bot with which you can manage events in different groups and so that people can easily make decisions.

### Import list for Event bot

<body>
<div class="import-list">
    <ul>
        <li>import psycopg2</li>
        <li>import asyncio</li>
        <li>import pandas as pd</li>
        <li>import openpyxl</li>
        <li>import logging</li>
        <li>import time</li>
        <li>import datetime</li>
    </ul>
</div>
</body>
# A more detailed account of what exactly the bot does.

<body>
<div class="technical-task" Color="red">
    <h2>For Administrator</h2>
    <table>
        <thead>
            <tr>
                <th>Requirement</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>The bot must have an admin menu that is accessible to a limited list of people (idtgs are maintained manually)</td>
                <td>called by the /Admin command</td>
            </tr>
            <tr>
                <td>The "Change greeting" button is available in the admin panel. The text is saved/replaced in notepad</td>
                <td></td>
            </tr>
            <tr>
                <td>The "Schedule a survey" button is available in the admin panel. As part of the call, the bot will ask sequentially: the text of the survey, the answer options (there may be no more than three), the regularity (buttons – weekly or one-time), the day of the week (if weekly regularity is selected, there may be several surveys within a week), time, the maximum number of participants, the time of notification of doubters (with a button "No" when such notification is not needed)</td>
                <td>as part of the survey planning, we receive the day of the week of the event, but the survey itself is sent to the group "-1" day from this event – if this newsletter falls on a weekday. If it falls on a day off, then you need to send the newsletter on Friday. After the end of the event day, the poll message is deleted from the group. For example: The event is scheduled for Monday (09/18/2023), -1 day is Sunday and since it is a day off, the message with the survey will be sent on Friday (09/15/2023), and on 09/19/2023 it will be deleted because 18.09 has already passed. the time of notification of doubters is filled in the time_maybe field and the bot sends a message to the group at the specified time, "-1" day from the day of the event: "<Name> your training decision affects the rest of the participants, please, if possible, specify in the survey the current status of your presence" The array <name> is formed from those who the date of the event in the maybe field was set to "?"</td>
            </tr>
            <tr>
                <td>The "Cancel survey" button is available in the admin panel. In response, the bot sends all valid weekly surveys (id, day of the week, time), the admin chooses which one to cancel and sends the id. The bot sets the cancel flag with the “X” flag for the sent id</td>
                <td></td>
            </tr>
            <tr>
                <td>The "Change schedule" button is available in the admin panel. The text is saved/replaced in notepad</td>
                <td></td>
            </tr>
            <tr>
                <td>The "Newsletter" button is available in the admin panel. The message sent by the admin to the bot will be posted in the selected group (the bot can be added to several groups)</td>
                <td></td>
            </tr>
            <tr>
                <td>The "Limit" button is available in the admin panel. The administrator will indicate the maximum number of participants in the list in response</td>
                <td></td>
            </tr>
            <tr>
                <td>The "Add" button is available in the admin panel. The bot specifies the event id, last name and first name. And adds an event to the table</td>
                <td></td>
            </tr>
            <tr>
                <td>The "Delete" button is available in the admin panel. The bot clarifies the event id, last name and first name/ And removes the event from the table</td>
                <td></td>
            </tr>
        </tbody>
    </table>
    <h2>For default user</h2>
    <table>
        <thead>
            <tr>
                <th>Requirement</th>
                <th>Description</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>When registering a user, if the service number was filled in, then the value – lenta is set in the relations field in the people table, otherwise - outside</td>
                <td></td>
            </tr>
            <tr>
                <td>From the pinned menu, you can call the /roster command In response, you will receive a list of the current survey (if there are several, then several messages)</td>
                <td>Message format: <br>Composition on <date>: <br>Last Name First Name maybe Last Name First Name maybe…</td>
            </tr>
            <tr>
                <td>In the pinned menu, you can call the /schedule command. In response, the bot will send a message from a text file</td>
                <td>The "Change schedule" button is available in the admin panel. The text is saved/replaced in notepad</td>
            </tr>
            <tr>
                <td>In the pinned menu, you can call the /doc command. In response, the bot will send a message from a text file</td>
                <td>The "Edit documents" button is available in the admin panel. The text is saved/replaced in notepad</td>
            </tr>
        </tbody>
    </table>
</div>
<div class="Reaction-buttons">
<h2>Reaction to buttons, waiting list, notifications:</h2>
    <h3>For button answ3</h3>    
    <p>5.1.1 When the user clicks the answ1 button in the survey: check if the user has already checked in on this date in the event table<br>
    5.1.1.1 If there is already and the maybe field is empty, then the user gets a push "Your vote has already been successfully counted".<br>
    5.1.1.2 If there is already and the maybe field is filled in, then the maybe field in the database is cleared and the user gets a push "The change of participation has been taken into account", and a message is also sent to the group "<Name> will definitely be at the training <date>".<br>
    5.1.1.3 If there was no user before, then check how many participants have already been recorded for the event (event table with id and date key),<br>
    5.1.1.3.1 if this is equal to or greater than the value of max_people (survey tables), then check the relations attribute from the people table<br>
    5.1.1.3.1.1 If a user with the value outside, then the waiting list is replenished by the logged-in user (the waiting and num_waiting fields of the event table). The user gets a push – "Your vote has been successfully counted, thank you! (the waiting list has been updated)."<br>
    5.1.1.3.1.2 If the user is with the lenta value, then in the event table (according to using the id and date keys), we find the user who has the maximum value specified in the external field (if no such user is found, then we immediately put him on the waiting list) and put him on the waiting list by setting values in the waiting and num_waiting fields. The registered user is simply added to the table by sending a push - "Your vote has been successfully counted, thank you! (the main cast has been updated)".  The bot sends a message to the group – "<p Name> moved to the waiting list"<br>
    5.1.1.3.2 If this is less than the value of max_people (survey tables), then simply add the event to the table without filling in the waiting and num_waiting fields. The user gets a push – "Your vote has been successfully counted, thank you! (the main cast has been updated)".<br></p>
    <h3>For button answ2</h3>
    <p>5.1.2 When the user clicks the answ2 button in the survey: check whether the user who has already checked in is already on this date in the event table <br>
    5.1.2.1 If the field maybe is already empty, then in the database we set the value "?" in the field maybe, and the user gets a push "Change of participation is taken into account", and also a message is sent to the group "<Name> may not be able to attend the training <date>".<br>
    5.1.2.2 If the field maybe is already available If filled in, then the user gets a push "Your vote has already been successfully counted".<br>
    5.1.2.3 If there was no user before, then check how many participants have already been registered for the event (event table with id and date key),
    5.1.2.3.1 if this is equal to or greater than the value of max_people (survey tables), then checking the relations attribute from the people table <br>
    5.1.2.3.1.1 If a user with the value outside, then the waiting list is filled in by the logged-in user (the waiting and num_waiting fields of the event table), as well as the maybe field is filled with the value "?". The user gets a push – "Your vote has been successfully counted, thank you! (the waiting list has been updated)." <br>
    5.1.2.3.1.2 If the user is with the lenta value, then in the event table (according to using the id and date keys), we find the user who has the maximum value specified in the external field (if no such user is found, then we immediately put the user on the waiting list).  and we put it on the waiting list by setting values in the waiting and num_waiting fields . We simply add the logged-in user to the table, and the maybe field is filled with the value "?". By sending a push - "Your vote has been successfully counted, thank you! (the main cast has been updated)".  The bot sends a message to the group – "<Last Name> moved to the waiting list" <br>
    5.1.2.3.2 If this is less than the value of max_people (survey tables), then simply add the event to the table without filling in the waiting and num_waiting fields, and the maybe field is filled with the value "?". The user gets a push – "Your vote has been successfully counted, thank you! (the main cast has been updated)". <br></p>
    <h3>For button answ3</h3>
    <p>5.1.3 When the user clicks the answ3 button in the survey: check whether the user who has already checked in is already on this date in the event table <br>
    5.1.3.1 if there is, then delete it from the table and send a push - "Change of participation is taken into account", and a message is also sent to the group "<Name> unfortunately will not be able to attend the training <date>". And also check for the date of the user event in the waiting list (the waiting and num_waiting fields are not empty)<br>
    5.1.3.1.1 If there are such users, then there is one whose num_waiting field has the maximum value and the waiting and num_waiting fields are cleared for him. <br>
    5.1.3.2 if not, then we send the user a push – "Thank you for warning! We'll be waiting for you next time."</p>
</div>
</body>
