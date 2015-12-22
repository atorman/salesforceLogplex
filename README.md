## Logging Salesforce User Activity with Heroku's Logplex

If you can't already tell, I'm huge advocate of logging user activity. There's something incredibly powerful about understanding what people did in the past. I guess it harkens back to my days as a high school history teacher where I would tell everyone on the first day of class that students who fail my class are doomed to repeat it.

In my quest for understanding how salesforce customers want to log activity and measure it, there are some consistent themes I've heard:
1. the use case always drives the granularity of the data we need to capture
2. while real-time isn't always necessary, it's almost always desired
3. I really want one place to go to for log data
4. if I have access to the raw log data, I can always slice-and-dice it the way I want in my reporting app of choice

One interesting solution that I've been playing with is capturing events in Salesforce orgs and sending them over to [Heroku](https://www.heroku.com/). If you haven't heard of Heroku before, you should check it out. It's a platform for developers to effectively deploy and manage their applications. One of the great advantages of Heroku is it's great add-on platform called [Elements](https://elements.heroku.com/). Whether it's cache, video processing, data storage, or monitoring, it's easy to plug Heroku apps into a great ecosystem of app providers.

Logging Salesforce user activity is pretty simple:
1. I created a polling app that runs on Heroku. In my case, I created a python script that polls Salesforce every minute to retrieve Setup Audit Trail events. But it could just as easily captured Login History, Data Leakage, Apex Limit Events, or really any object accessible via the [Salesforce API](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_objects_list.htm).
2. The python script writes Salesforce user events to the Heroku logging system called [LogPlex](https://blog.heroku.com/archives/2013/11/7/logplex-down-the-rabbit-hole)
3. LogPlex is integrated with a series of add-ons including Logentries, Sumologic, and PaperTrail. It can also be integrated into other back end systems like a SIEM tool or notification apps like PagerDuty

The advantages of this solution include:

* it's near real-time (or as real time as the frequency of the polling app you create)
* it has the ability to further integrate events from other Heroku apps that you've built
* Heroku has a great add-on ecosystem that makes it easy to turn these events into insights

The disadvantages of this solution include:

* Heroku's LogPlex only persists the last 1500 events and can be lossy since it was really intended to be used * for logging performance trends rather than security events like escalation of privileges.
the polling app will count against API limits. If it polls every minute, it will cost you 1440 API calls per day.

![alt tag] (https://raw.github.com/atorman/salesforceLogplex/master/img/logentries.png)

## Installation

Sign up for a Heroku account if you don't already have one. 

1. Download a ZIP of the repository. 
2. Uncompress the files.
3. Use git to push the files to Heroku. If you've never tried this before, check out the great resources in the [Heroku dev center](https://devcenter.heroku.com/articles/getting-started-with-python#introduction)

## Configuration and Usage

You will need to add-on the monitoring and logging apps from Elements. This is easily done with the FIND MORE ADD-ONS link on the dashboard or adding it through the CLI - heroku addons:create logentries:le_tryit.

![alt tag] (https://raw.github.com/atorman/salesforceLogplex/master/img/herokuDashboard.png)

You will also need to add key configuration variables like authentication, API version, and polling time in the settings page.

![alt tag] (https://raw.github.com/atorman/salesforceLogplex/master/img/configVars.png)

## Credit

Contributors include:

* Adam Torman created and orchestrated the majority of the repository
* Jeff Douglas' [blog post](http://blog.jeffdouglas.com/2012/09/07/node-demo-with-force-com-streaming-api-socket-io/) that demonstrated streaming API onto apps in Heroku

This repo is As-Is. All pull requests are welcome.