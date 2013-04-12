# Create your views here.
from models import *
from django.shortcuts import render_to_response
from cicero_search import *
from django.template import RequestContext, loader
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from datetime import timedelta, date
from django.db.models import Count
import json
from JSON_exporter import get_top_tweeters


########################################
## Search by address, display results ##
########################################


def WhichRep(request):
    l = LegislatorFinder()
    if 'q' in request.GET:
        address = request.GET['q']
        try:
            l.geocode_address(address)
        except ValueError:
            place_list = [{'address': place[0], 'lat': place[1], 'lng': place[2]} for place in l.places]
            return render_to_response('intermediate_error.html',
                {'places': place_list})
        except LookupError:
            return render_to_response('intermediate_error.html')
        l.find_leg_districts()
    if 'lat' in request.GET:
        l.find_leg_districts(lat=request.GET['lat'], lng=request.GET['lng'])
    upper_leg = Officials.objects.filter(district=l.upper).filter(chamber="upper").filter(active="True")[0]
    try:
        lower_leg = Officials.objects.filter(district=l.lower).filter(chamber="lower").filter(active="True")[0]
    except:
        lower_leg = None
    try:
        upper_office = OfficialOffices.objects.filter(office_legid=upper_leg.legid).order_by('name').values()[0]
    except:
        upper_office = None
    try:
        lower_office = OfficialOffices.objects.filter(office_legid=lower_leg.legid).order_by('name').values()[0]
    except:
        lower_office = None
    return render_to_response('intermediate.html',
        {"upper": upper_leg,
        "lower": lower_leg,
        "upperoffice": upper_office,
        "loweroffice": lower_office})

####################
## PA Tweets Page ##
####################


def pa_tweets(request):
    """Request for pa-tweets page, contains the last 30 tweets by members of the General Assembly"""
    tweets_oembed = OfficialTweets.objects.order_by('-timestamp').exclude(oembed="")
    paginator = Paginator(tweets_oembed, 40)  # Show 40 tweets per page

    page = request.GET.get('page')
    try:
        page = int(request.GET.get("page", '1'))
    except ValueError:
        page = 1

    try:
        tweets_oembed = paginator.page(page)
    except (InvalidPage, EmptyPage):
        tweets_oembed = paginator.page(paginator.num_pages)

    today = date.today()
    d = timedelta(days=30)
    filter_date = today - d
    tweets = OfficialTweets.objects.filter(timestamp__gte=filter_date).extra({'created': "date(timestamp)"}).values('created').annotate(created_count=Count('tweet_key')).order_by('-created')
    tweet_list = []
    for tweet in tweets:
        x = tweet['created'].strftime("%Y-%m-%d")
        y = tweet['created_count']
        tweet_list.append({"date": x, "count": y})
    top_tweeters = get_top_tweeters(7)

    return render_to_response('all_tweets.html',
        {'tweet_list': json.dumps(tweet_list),
        'top_tweeters': json.dumps(top_tweeters),
        "tweets": tweets_oembed})

####################
##  Profile Page  ##
####################


def profile(request, profile_legid):
    official_object = Officials.objects.only("fullname", "photourl", "party", "chamber").get(legid=profile_legid)
    # official_object.get_offices()
    official_object.help_vars()

    ## Get Tweets ##
    twitter_id = Officials.objects.get(legid=profile_legid).twitter
    tweets = OfficialTweets.objects.defer("oembed").filter(legid=profile_legid).order_by('-timestamp').select_related()[:10]
    for tweet in tweets:
        tweet.form_url(twitter_id)

    ## Get Offices ##
    offices = OfficialOffices.objects.filter(office_legid=profile_legid).values()

    ## Get Votes ##
    votes = PaLegisVotes.objects.filter(legid=profile_legid).order_by('-date').select_related()[:10]

    ## Get FB Posts ##
    fb_posts = FbData.objects.filter(legid=profile_legid).order_by('-timestamp').select_related()[:10]

    ## Get Press Releases ##
    press_releases = OfficialPressReleases.objects.only("pr_title", "pr_date", "pr_url").filter(pr_legid=profile_legid).order_by('-pr_date').select_related()[:30]
    filtered_press_releases = filter_press_releases(press_releases)

    ## Ideology and Graph Data ##
    official_object.get_pref_rank()
    try:
        ideology = Preferences.objects.get(legid=profile_legid).ideology
        graph_data = get_kdensity_data(chamber_to_get=official_object.chamber)
    except:
        ideology = None
        graph_data = None

    return render_to_response('info.html',
        {'official': official_object,
        "legid": profile_legid,
        "graph_data": graph_data,
        "tweets": tweets,
        "votes": votes,
        "fb_posts": fb_posts,
        "press_releases": filtered_press_releases,
        "ideology": ideology,
        "offices": offices},
        context_instance=RequestContext(request))

###############
## Home Page ##
###############


def search_form(request):
    user = request.user
    return render_to_response('index.html', {'user': user})

#######################
## About StateRep.Me ##
#######################


def about_myrep(request):
    """Returns about page"""
    return render_to_response('about.html')

########################
## Browse Legislators ##
########################


def legislator_list(request):
    """Returns page that has list of browse-able state legislators"""
    upper_leg = Officials.objects.filter(chamber="upper", active="True").order_by('district')
    lower_leg = Officials.objects.filter(chamber="lower", active="True").order_by('district')
    return render_to_response('all_legislators.html',
        {'senators': upper_leg,
        'representatives': lower_leg})


#################
## At a Glance ##
#################

# def at_a_glance(request):
#     """Primary Web Application for StateRep.Me"""
#     ## Get Tweets from Last 30 Days ##
#     today = date.today()
#     d = timedelta(days=30)
#     filter_date = today - d
#     tweets = OfficialTweets.objects.filter(timestamp__gte=filter_date).extra({'created': "date(timestamp)"}).values('created').annotate(created_count=Count('tweet_key')).order_by('-created')
#     tweet_list = []
#     for tweet in tweets:
#         x = tweet['created'].strftime("%Y-%m-%d")
#         y = tweet['created_count']
#         tweet_list.append({"date": x, "count": y})
#     top_tweeters = get_top_tweeters(7)
#     d = timedelta(days=2)
#     filter_date = date.today() - d
#     tweets = OfficialTweets.objects.filter(timestamp__gte=filter_date).order_by('-timestamp')
#     return render_to_response('at_a_glance.html',
#         {'tweet_list': json.dumps(tweet_list),
#         'top_tweeters': json.dumps(top_tweeters),
#         'tweets': tweets})
