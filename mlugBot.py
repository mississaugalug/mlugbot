################################################################################
################################################################################
# Name:          mlugBot.py
# Usage:
# Description:
# Created:       2014-11-09
# Last Modified:
# Modified by Victor Mendonca - http://mississaugalug.ca
# License: Released under the terms of the GNU GPL license
################################################################################
################################################################################

"""
## Based on Twisted Matrix Laboratories Framework ##

=> API Doc
http://twistedmatrix.com/documents/current/api/twisted.words.protocols.irc.IRCClient.html

=> How to Clients
http://twistedmatrix.com/documents/10.1.0/core/howto/clients.html
"""

"""
A modified IRC log bot that also logs channel's events to a file.

Run this script with two arguments, the channel name the bot should
connect to, and file to log to, e.g.:

    $ python ircLogBot.py test test.log

will log channel #test to the file 'test.log'.

To run the script:

    $ python ircLogBot.py <channel> <file>
"""


# twisted imports
from twisted.words.protocols import irc
from twisted.internet import reactor, protocol
from twisted.internet.task import LoopingCall
from twisted.python import log

# system imports
import time, sys, re

# For URL Grabbing
import urllib
import urllib2
from BeautifulSoup import BeautifulSoup
from re import findall

# for fortune
import subprocess
import os

# For Twitter (man)
from twitter import *
import random
from twitter_app_credentials import *
twitter = Twitter(
auth=OAuth(access_token_key, access_token_secret, consumer_key, consumer_secret))

# For Twitter feed
#import threading
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
twitter_userlist = ['victorbrca', 'MississaugaLUG']

myNick = (sys.argv[1])


class MessageLogger:
    """
    An independent logger class (because separation of application
    and protocol logic is a good thing).
    """
    def __init__(self, file):
        self.file = file

    def log(self, message):
        """Write a message to the file."""
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.file.write('%s %s\n' % (timestamp, message))
        self.file.flush()

    def close(self):
        self.file.close()


class LogBot(irc.IRCClient):
    """A logging IRC bot."""

    nickname = myNick

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.logger = MessageLogger(open(self.factory.filename, "a"))
        self.logger.log("[connected at %s]" %
                        time.asctime(time.localtime(time.time())))

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.logger.log("[disconnected at %s]" %
                        time.asctime(time.localtime(time.time())))
        self.logger.close()

    # callbacks for events

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.join(self.factory.channel)

    def joined(self, channel):
        """This will get called when the bot joins the channel."""
        self.logger.log("[I have joined %s]" % channel)

    def twitterFeed(self, channel):
        #chan = channel
        twitter_userlist = ['victorbrca', 'MississaugaLUG', 'BobJonkman']
        #print twitter_userlist
        #print "This is the thread running"
        for user in twitter_userlist:
            RawTweet = twitter.statuses.user_timeline(screen_name=user,count=1)[0]
            RawTweetDate = RawTweet['created_at']
            UTCRawTweetDate = re.sub(r'\+[0-9]{4}', 'UTC', RawTweetDate)
            print "last post raw date is %s" % UTCRawTweetDate
            TweetDateToTime = datetime.strptime(UTCRawTweetDate, '%a %b %d %H:%M:%S %Z %Y')
            TweetDate = TweetDateToTime.strftime('%Y-%b-%d %H:%M')
            #ptime = ptimetostr
            #pdate = datetime.strptime(date, '%Y-%b-%d %H:%M')
            GetFiveMinAgo = datetime.utcnow() - timedelta(minutes = 5)
            FiveMinAgo = GetFiveMinAgo.strftime('%Y-%b-%d %H:%M')
            print "Tweet time is: %s - Time 5 mins ago: %s" % (TweetDate, FiveMinAgo)
            if FiveMinAgo < TweetDate:
                CurrentTime = datetime.utcnow()
                diff = relativedelta(CurrentTime, TweetDateToTime)
                print "%s:%s" % (diff.minutes, diff.seconds)
                if diff.minutes < 1:
                    Ago = "%s seconds ago" % diff.seconds
                else:
                    Ago = "%s minutes ago" % diff.minutes
                tweet = ("@%s: %s (%s)" % (RawTweet["user"]["screen_name"], RawTweet["text"], Ago))
#                print tweet
                msg = tweet.encode('utf-8')
                self.sendLine("PRIVMSG %s :%s" % (channel, msg))
                #return
#            else:
#                print "no new tweets"
            #time.sleep(10)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""

        user = user.split('!', 1)[0]
        self.logger.log("<%s> %s" % (user, msg))

        # Check to see if they're sending me a private message
        if channel == self.nickname:
            #msg = "Why don't you get a room with someone else. I don't do privates."
            msg = "Sorry, I don't support private messages."
            self.msg(user, msg)
            return

    ###
    ## Handles if a message directed at me ###
    ###

    # Hello
        elif re.search(r"%s[:,] hello" % self.nickname, msg):
            msg = "Hello %s, I'm the MLUG channel bot. Type '!help' to view how I can help you." % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # Quick help options
        elif re.search(r'%s[:,] (help|ping)$' % self.nickname, msg):
            msg = "Commands start with '!'\nAvailable options: help (full help), about, motd, history (chat history), mhistory (history of mlug), meet, wiki, man. \nFun options: bash, whoareyou, make me a sandwich, moo, fortune, facts"
            self.msg(channel, msg)

    # Full help options
        elif msg == "!help":
            h=open("lib/help")
            hlp = h.read()
            for line in hlp.split(os.linesep):
                msg = ("%s" % line)
                self.msg(channel, msg)
                self.logger.log("<%s> %s" % (self.nickname, msg))
                #time.sleep(.2)
            h.close()

    # About
        elif msg == "!about":
            f=open("lib/about")
            about = f.read()
            for line in about.split(os.linesep):
                msg = ("%s" % line)
                self.msg(channel, msg)
                self.logger.log("<%s> %s" % (self.nickname, msg))
                #time.sleep(.8)
            f.close()

    # Displays motd
        #elif re.search(r'%s[:,] motd$' % self.nickname, msg):
        elif msg == "!motd":
            f=open("lib/motd")
            motd = f.read()
            for line in motd.split(os.linesep):
                msg = ("%s" % line)
                self.msg(channel, msg)
                self.logger.log("<%s> %s" % (self.nickname, msg))
                #time.sleep(.8)
            f.close()

    # Displays history in a private window
        elif msg == "!history":
            if channel == '#mlug-priv':
                self.msg(channel, "%s: I'm sorry but we don't log messages here" % user)
                return
            elif channel != '#mlug-ca':
                self.msg(channel, "%s: I don't think I should be here. This channel is not registered on my database" % user)
                return
            self.msg(channel, "%s: Give me a sec. I'll open 25 lines of history for mlug's channel in a private window." % user)
            self.logger.log("<%s> %s" % (self.nickname, msg))
            count = 25
            logfile=open("var/log/irc/current.log")
            for i in range(count):
                 #import time
                 line=logfile.next().strip()
                 msg = (line)
                 self.msg(user, msg)
                 time.sleep(.8)
            logfile.close()

    # Displays mlug history
        elif msg == "!mhistory":
            f=open("lib/history")
            history = f.read()
            for line in history.split(os.linesep):
                msg = ("%s" % line)
                self.msg(user, msg)
                self.logger.log("<%s> %s" % (self.nickname, msg))
                #time.sleep(.8)
            f.close()

    # Meet
        elif msg == "!meet":
            url = 'http://mississaugalug.ca/'
            soup = BeautifulSoup(urllib2.urlopen("%s" % url))

            getEventTitles = soup.findAll(itemprop="name")

            cnt = 0
            for title in getEventTitles:
                thisTitle = title.getText()
                if thisTitle == "MLUG Monthly Meet":
                    positionalP = cnt
                    break
                cnt += 1

            title = soup.findAll(itemprop="name")[positionalP].getText()
            month = soup.findAll("div", {"class": "dp-upcoming-text-month"})[positionalP].getText()
            day = soup.findAll("div", {"class": "dp-upcoming-text-day"})[positionalP].getText()
            startDate = soup.findAll(itemprop="startDate")[positionalP].getText()
            time = startDate.split('-', 1)[0].split(' ', 1)[1]
            location = soup.findAll("meta", {"itemprop": "location"})[positionalP]['content']
            spltLoc = location.rsplit(',', 2)[0]

            meet = 'The next \"%s\" will be on %s %s, %sat %s' % (title, month, day, time, spltLoc)
            msg = meet.encode('utf-8')
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # Wikipedia
        elif re.search(r"!wiki .*", msg):
            searchstring = msg.split(' ', 1)[1]
            article = searchstring
            article = urllib.quote(article)

            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent', 'Mozilla/5.0')] #wikipedia needs this

            resource = opener.open("http://en.wikipedia.org/wiki/" + article)
            data = resource.read()
            resource.close()
            soup = BeautifulSoup(data)
            soup = soup.find('div',id="bodyContent").p
            summary = soup.getText()
            utfsoup = summary.encode('utf-8')
            if re.search(r'refer to', utfsoup):
                msg = "^ Too many options on wikipedia"
            else:
                msg = "^ %s" % utfsoup
            self.msg(channel, msg)

    # man
        elif re.search(r"!man .*", msg):
            command = msg.split(' ', 1)[1]
            #print command
            sections = ['1', '2', '3', '4', '5', '6', '7', '8']
            for section in sections:
                url = "http://linux.die.net/man/%s/%s" % (section, command)
                try:
                    urllib2.urlopen(url)
                except urllib2.HTTPError:
                        if section == "8":
                            commandout = "Command not found"
                            self.msg(channel, commandout)
                else:
                    soup = BeautifulSoup(urllib2.urlopen("%s" % url))
                    oneline = soup.fetch('p')[0].getText().splitlines()[0]
                    w = re.sub(r'Synopsis.*$', '', oneline)
                    whatis = w.encode('utf-8')
                    self.msg(channel, whatis)
                    break

    # Fun commands
        elif msg == "!fun":
            f=open("lib/fun")
            fun = f.read()
            for line in fun.split(os.linesep):
                msg = ("%s" % line)
                self.msg(channel, msg)
                self.logger.log("<%s> %s" % (self.nickname, msg))
                #time.sleep(.8)
            f.close()

    # Start Twitter feed
        elif msg == "!starttwitter" and user == "victorbrca":
            print "Twitter started"
            task = LoopingCall(self.twitterFeed, channel)
            task.start(300)
#            twitter_thread = TwitterThread(channel)
#            twitter_thread.start()


    # swearing at me
        elif re.search(r'%s[:,] .*(fuck|cunt|pussy|cock|asshole|shit|fag|slut|bitch)' % self.nickname, msg):
            swear = re.search(r'(fuck|cunt|pussy|cock|asshole|shit|fag|slut|bitch)', msg)
            msg = "%s: No you are the %s!" % (user, swear.group())
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
            msg = "%s: Now stop swearing!" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # Unknown option
        elif re.search(r'%s[:,] .+' % self.nickname, msg):
            msg = "I don't understand that command"
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # Talking to me
        elif re.search(r'%s[:,] ?$' % self.nickname, msg):
            # someone is talking to me, lets respond:
            msg = "%s: sup? Say \"%s: help\" for a list of commands" % (user, self.nickname)
            self.say(channel, msg)


### Fun Commands ###

    # Bash tip
        elif msg == "!bash":
            #twitter = Twitter(
    #auth=OAuth(access_token_key, access_token_secret, consumer_key, consumer_secret))
            rawtimeline = twitter.statuses.user_timeline(screen_name="bashcookbook")
            cleanup = ['RT','@']
            status = []
            for line in rawtimeline:
                tweet = ("%s: %s" % (line["user"]["screen_name"], line["text"]))
                if not any(cleanup in tweet for cleanup in cleanup):
                    status.append(tweet)
            status = (random.choice(status))
            decoded = status.encode('utf-8')
            msg = "^ @%s" % decoded
            self.msg(channel, msg)
#            bashtp=open("/tmp/bashcookbook")
#            msg = bashtp.read()
#            self.msg(channel, msg)
#            self.logger.log("<%s> %s" % (self.nickname, msg))
#            bashtp.close()

    # Who are you
        #elif re.search(r'%s[:,] who ?are ?you?' % self.nickname, msg):
        elif msg == "!whoareyou":
            msg = "%s: Who Are You is the eighth studio album by English rock band The Who, released through Polydor Records in the United Kingdom and MCA Records in the United States. It peaked at number 2 on the US charts and number 6 on the UK charts. It is The Who's last album with Keith Moon as the drummer; Moon died twenty days after the release of this album." % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
            time.sleep(2)
            msg = "%s: Being serious now, I can't tell you who I am. But I'll give you a hint... \"I've got no strings on me\"" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # make me a sandwich
        elif re.search(r'!make me a sandwich', msg):
            msg = "%s: what? make it yourself!" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

        # sudo make me a sandwich
        elif re.search(r'!sudo make me a sandwich', msg):
            msg = "%s: okay." % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # moo
        elif msg == "!moo":
            self.msg(channel, '                 (__)')
            self.msg(channel, '                 (oo)')
            time.sleep(.5)
            self.msg(channel, '           /------\/ ')
            self.msg(channel, '          / |    ||  ')
            time.sleep(.5)
            self.msg(channel, '         *  /\---/\  ')
            self.msg(channel, '            ~~   ~~  ')
            self.msg(channel, '...\"Have you mooed today?\"...\n')

    # Fortune
        elif msg == '!fortune':
            f = subprocess.Popen('./lib/cowsay.sh', stdout=subprocess.PIPE)
            fortune = f.communicate()[0]
            for line in fortune.split(os.linesep):
                #msg = line.strip()
                msg = ("%s" % line)
                self.msg(channel, msg)
                self.logger.log("<%s> %s" % (self.nickname, msg))

    # Facts - who created me, swear count (need logger)
        elif msg == "!facts":
            msg = "I'm not programmed with this option yet"
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))
#            f=open("lib/fun")
#            fun = f.read()
#            for line in fun.split(os.linesep):
#                msg = ("%s" % line)
#                self.msg(channel, msg)
#                self.logger.log("<%s> %s" % (self.nickname, msg))
#                #time.sleep(.8)
#            f.close()

    ###
    ## Messages not directed to me ###
    ###

    # Swearing
        elif re.search(r'(fuck|cunt|pussy|cock|asshole|shit|fag|slut|bitch)', msg):
            msg = "%s: No swearing!" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # yelling
        elif re.search(r'^([^a-z]+[\s|\W][A-Z]{2,})', msg):
            msg = "%s: Please, NO YELLING IN THE CHAT!" % user
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))

    # Grabs URL
        elif re.search(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", msg):
            urls = findall(r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+", msg)
            if urls:
                #print urls
                url = urls[0]
                #print url
                soup = BeautifulSoup(urllib2.urlopen("%s" % url))
                finalsoup = soup.title.string
                utfsoup = finalsoup.encode('utf-8')
                msg = "^ %s" % utfsoup
                self.msg(channel, msg)

    # Heard my name
        elif re.search(r'%s' % self.nickname, msg):
            msg = "%s: I heard you saying my name. Do you need help? Type \"%s: help\" or \"!help\" if you do." % (user, self.nickname)
            self.msg(channel, msg)
            self.logger.log("<%s> %s" % (self.nickname, msg))


    ###
    ## Channel actions
    ###

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.logger.log("* %s %s" % (user, msg))


    ###
    ## irc callbacks
    ###"""

    def userRenamed(self, oldname, newname):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.logger.log("%s is now known as %s" % (old_nick, new_nick))

    def irc_JOIN(self, prefix, params):
        """ Welcomes user """
        nick = prefix.split('!', 1)[0]
        if nick != self.nickname:
            channel = params[-1]
            msg = "%s: welcome to %s" % (nick, channel)
            self.msg(channel, msg)
        elif nick == self.nickname:
            channel = params[-1]
            msg = "Yo yo... %s is in the hood bitches!" % nick
            self.msg(channel, msg)

    def userKicked(self, kickee, channel, kicker, message):
        """ Called when a user is kicked from the channel """
        msg = "Haha!! %s just got kicked from the channel" % (kickee)
        self.msg(channel, msg)

    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '1'



class LogBotFactory(protocol.ClientFactory):
    """A factory for LogBots.

    A new protocol instance will be created each time we connect to the server.
    """

    def __init__(self, channel, filename):
        self.channel = channel
        self.filename = filename

    def buildProtocol(self, addr):
        p = LogBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, reconnect to server."""
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed:", reason
        reactor.stop()


if __name__ == '__main__':
    # initialize logging
    log.startLogging(sys.stdout)

    # create factory protocol and application
    f = LogBotFactory(sys.argv[2], sys.argv[3])

    # connect factory to this host and port
    reactor.connectTCP("irc.freenode.net", 6667, f)

    # run bot
    reactor.run()
