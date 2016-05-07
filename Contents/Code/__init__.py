# Data18-Content
import re
import random
from datetime import datetime

# this code was borrowed from the Excalibur Films Agent. April 9 2013
# URLS
VERSION_NO = '1.2015.03.28.2'
EXC_BASEURL = 'http://www.data18.com/'
EXC_SEARCH_MOVIES = EXC_BASEURL + 'search/?k=%s&t=0'
EXC_MOVIE_INFO = EXC_BASEURL + 'content/%s'
XP_SCENE_LINK = ''.join(['//div[contains(@class,"bscene")]',
                         '//span//a[contains(@href,"content")]'])
USER_AGENT = ''.join(['Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; ',
                      'Trident/4.0; SLCC2; .NET CLR 2.0.50727; ',
                      '.NET CLR 3.5.30729; .NET CLR 3.0.30729; ',
                      'Media Center PC 6.0)'])

titleFormats = r'DVD|Blu-Ray|BR|Combo|Pack'

XPATHS = {
    # Parse Document
    'network': '//a[contains(@href,"http://www.data18.com/sites/") \
                and following-sibling::i[position()=1][text()="Network"]]',
    'site': '//a[contains(@href,"http://www.data18.com/sites/") \
                and following-sibling::i[position()=1][text()="Site"]]',
    'studio': '//a[contains(@href,"http://www.data18.com/studios/") \
                and following-sibling::i[position()=1][text()="Studio"]]',
    # Search Result Xpaths
    'scene-container': '//div[contains(@class,"bscene")]',
    'scene-link': '//span//a[contains(@href,"content")]',
    'scene-site': '//p[contains(text(), "Site")]]',
    'scene-network': '//p[contains(text(), "Network")]]',
    'scene-cast': '//p[contains(text(), "Cast")]]',

    # Actor in site Search results
    'site-link': '//select//Option[text()[contains(\
                        translate(., "$u", "$l"), "$s")\
                        ]]//@value',
    'actor-site-link': '//a[text()[contains(\
                            translate(., "$u", "$l"), "$s")\
                            ]]//@href',
    # Content Page Xpaths
    'release-date': '//p[text()[contains(\
                        translate(.,"relasdt","RELASDT"),\
                        "RELEASE DATE")]]//a',
    'release-date2': '//*[span[contains(text(),"Release date")]]\
                    //a[@title="Show me all updates from this date"]',
    'release-date3': '//*[span[contains(text(),"Release date")]]\
                    /span[@class="gen11"]/b',
    # Images
    'poster-image': '//img[@alt="poster"]',
    'single-image-url': '//img[contains(@alt,"image")]/..',
    'single-poster-image': '//img[@alt= "image"]',
    'src-single-image': '//img[contains(@alt,"image")]',
    'video-poster': '//img[@alt="Play this Video"]',
    'video-poster-alternate': '//*//iframe[contains(@src,"player.php")][1]',
    # MEtadata
    'genre': '//*[b[contains(text(),"Categories")]]//a[contains(@href, ".html")]',
    'summary': '//*[b[contains(text(),"Story:")]]',
    'actor': '//*[b[contains(text(),"Starring:")]]//a[@class="bold"]'
}

def Start():
    HTTP.CacheTime = CACHE_1DAY
    HTTP.SetHeader('User-agent', USER_AGENT)


def parse_document_date(html):
    try:
        try:
            curyear = html.xpath(XPATHS['release-date'])[0].get('href')
            curyear_group = re.search(r'(\d{8})', curyear)
            curdate = curyear_group.group(0)
            curdate = Datetime.ParseDate(curdate).date()
        except:
            try:
                date = html.xpath(XPATHS['release-date2'])[0].text_content()
                curdate = datetime.strptime(date, '%B %d, %Y').date()
            except:
                date = html.xpath(XPATHS['release-date3'])[0].text_content()
                curdate = Datetime.ParseDate(date).date()
                curdate = curdate.replace(day=1)
                #Log('curdate : '+date)
    except:
        curdate = None
    return curdate


def parse_document_network(html):
    # Network
    try:
        return html.xpath(XPATHS['network'])[0].text_content().strip()
    except:
        return None

def parse_document_studio(html):
    # Network
    try:
        return html.xpath(XPATHS['studio'])[0].text_content().strip()
    except:
        return None


def parse_document_site(html):
    # Site
    try:
        return html.xpath(XPATHS['site'])[0].text_content().strip()
    except:
        return None


def parse_document_title(html):
    # Title
    return html.xpath('//div/h1/text()')[0].strip()


def format_search_title(title, curdate, network, site):
    if title.count(', The'):
        title = 'The ' + title.replace(', The', '', 1)
    extra = '/'.join([e for e in [network, site] if e])
    extra = ' '.join([e for e in [str(curdate), extra] if e]).strip()

    if len(extra) > 0:
        title = title + ' (' + extra + ')'
    return title.strip()


def xpath_prepare(xpath, search):
    xpath = xpath.replace("$u", search.upper())
    xpath = xpath.replace("$l", search.lower())
    xpath = xpath.replace("$s", search.lower())
    return xpath


def find_option_value(searchURL, search_results, search):
    xp = xpath_prepare(XPATHS['site-link'], search)
    Log('xPath: ' + xp)
    try:
        searchURL = search_results.xpath(xp)[0]
    except:
        xp = xpath_prepare(XPATHS['site-link'].lower(), search)
        Log('xPath: ' + xp)
        searchURL = search_results.xpath(xp)[0]
    return searchURL


def search_na(results, media_title, year, lang):
    """
    Since Actor in Site scenes are not appearing in the search we
    need to do a bit of trickery to get them.
    """
    Log('Alternative search for N.A. websites')
    # Commenting out as it's not being used
    # actors = media_title.split(' in ')[0].split(',')
    actors_url_parts = media_title.split(' in ')[0]
    actors_url_parts = actors_url_parts.lower().replace(' ', '_')
    actors_url_parts = actors_url_parts.split(',')

    na_url_site = media_title.split(' in ', 1)[1]
    Log('Search URL: ' + na_url_site)

    # Take the first actor and the website name to search
    query_actor = actors_url_parts[0].replace('-', '')
    query_actor = String.StripDiacritics(query_actor)
    query_actor = String.URLEncode(query_actor)

    searchURL = EXC_BASEURL + query_actor
    Log('Search URL: ' + searchURL)

    try:
        search_results = HTML.ElementFromURL(searchURL)
    except:
        searchURL = EXC_BASEURL + 'dev/' + query_actor
        Log('Search URL: ' + searchURL)
        search_results = HTML.ElementFromURL(searchURL)

    try:
        searchURL = find_option_value(searchURL, search_results, na_url_site)
    except:
        try:
            searchURL = find_option_value(
                searchURL, search_results, re.sub(r'[\'\"]', '', na_url_site))
        except:
            search_results = HTML.ElementFromURL(searchURL + '/sites/')
            xp = xpath_prepare(XPATHS['actor-site-link'], na_url_site)
            Log('xPath: ' + xp)
            searchURL = search_results.xpath(xp)[0]

    search_results = HTML.ElementFromURL(searchURL)

    #searchURL = EXC_BASEURL + query_actor + '/sites/' + na_url_part + '.html'
    Log('Search URL: ' + searchURL)
    # try:
    #     search_results = HTML.ElementFromURL(searchURL)
    # except:
    #     searchURL = EXC_BASEURL +'dev/' + query_actor + '/sites/' + na_url_part + '.html'
    #     search_results = HTML.ElementFromURL(searchURL)
    count = 0
    for movie in search_results.xpath(XP_SCENE_LINK):
        movie_HREF = movie.get("href").strip()
        Log('Movie HREF: ' + movie_HREF)
        current_name = movie.text_content().strip()
        Log('New title: ' + current_name)
        current_ID = movie.get('href').split('/', 4)[4]
        Log('New ID: ' + current_ID)

        try:
            movieResults = HTML.ElementFromURL(movie_HREF)
            curdate = parse_document_date(movieResults)
            if curdate is None:
                Log('Date: No date found')
                score = 100 - \
                    Util.LevenshteinDistance(
                        media_title.lower(), current_name.lower())
                curyear = ''
                curdate = ''
            else:
                curyear = str(curdate.year)
                # Commenting as not being used
                # curmonth = str(curdate.month)
                # curday = str(curdate.day)
                curdate = str(curdate)
                Log('Found Date = ' + curdate)
                score = 100 - \
                    Util.LevenshteinDistance(
                        media_title.lower(), current_name.lower()) - \
                    Util.LevenshteinDistance(year, curyear)
                Log('It Worked ******** Score: {}'.format(score))
        except (IndexError):
            score = 100 - \
                Util.LevenshteinDistance(
                    media_title.lower(), current_name.lower())
            curyear = ''
            curdate = ''
            Log('Date: No date found (Exception)')
        if score >= 45:
            network = parse_document_network(movieResults)
            site = parse_document_site(movieResults)
            current_name = format_search_title(
                current_name, curdate, network, site)

            Log('Found:')
            Log('    Date: ' + curdate)
            Log('    ID: ' + current_ID)
            Log('    Title: ' + current_name)
            Log('    URL: ' + movie_HREF)
            results.Append(
                MetadataSearchResult(id=current_ID,
                                     name=current_name,
                                     score=score,
                                     lang=lang))
        count += 1
    results.Sort('score', descending=True)


class EXCAgent(Agent.Movies):
    name = 'Data18-Content'
    languages = [Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']
    primary_provider = True

    def search(self, results, media, lang):
        Log('Data18 Version : ' + VERSION_NO)
        Log('**************SEARCH****************')
        title = media.name
        content_id = False

        if media.name.isdigit():
            Log('Media.name is numeric')
            content_id = True
            contentURL = EXC_MOVIE_INFO % media.name
            html = HTML.ElementFromURL(contentURL)
            curdate = parse_document_date(html)

            network = parse_document_network(html)
            site = parse_document_site(html)
            title = parse_document_title(html)

            title = format_search_title(title, curdate, network, site)
            results.Append(
                MetadataSearchResult(id=media.name,
                                     name=title,
                                     score='100',
                                     lang=lang))

        if media.primary_metadata is not None:
            title = media.primary_metadata.title

        year = media.year
        if media.primary_metadata is not None:
            year = media.primary_metadata.year
            Log('Searching for Year: ' + year)

        Log('Searching for Title: ' + title)

        if len(results) == 0:
            #query = String.URLEncode(String.StripDiacritics(title.replace('-','')))
            query = String.URLEncode(String.StripDiacritics(title))

            searchUrl = EXC_SEARCH_MOVIES % query
            Log('search url: ' + searchUrl)
            searchResults = HTML.ElementFromURL(searchUrl)
            # Commenting out as not being used
            # searchTitle = searchResults.xpath('//title')[0].text_content()
            count = 0
            for movie in searchResults.xpath(XP_SCENE_LINK):
                movieHREF = movie.get("href").strip()
                Log('MovieHREF: ' + movieHREF)
                curName = movie.text_content().strip()
                Log('newTitle: ' + curName)
                curID = movie.get('href').split('/', 4)[4]
                Log('newID: ' + curID)
                try:
                    movieResults = HTML.ElementFromURL(movieHREF)
                    curdate = parse_document_date(movieResults)
                    if curdate is None:
                        Log('Date: No date found')
                        score = 100 - \
                            Util.LevenshteinDistance(
                                title.lower(), curName.lower())
                        curyear = ''
                        curdate = ''
                    else:
                        curyear = str(curdate.year)
                        # Commenting out as not being used
                        # curmonth = str(curdate.month)
                        # curday = str(curdate.day)
                        curdate = str(curdate)
                        Log('Found Date = ' + curdate)
                        score = 100 - \
                            Util.LevenshteinDistance(
                                title.lower(), curName.lower()) - \
                            Util.LevenshteinDistance(year, curyear)
                        Log('It Worked ******** Score: {}'.format(score))
                except (IndexError):
                    score = 100 - \
                        Util.LevenshteinDistance(
                            title.lower(), curName.lower())
                    curyear = ''
                    curdate = ''
                    Log('Date: No date found (Exception).  Score: {}'.format(score))
                if score >= 45:
                    network = parse_document_network(movieResults)
                    site = parse_document_site(movieResults)

                    curName = format_search_title(
                        curName, curdate, network, site)

                    # Log('Found:')
                    #Log('    Date: ' + curdate)
                    #Log('    ID: ' + curID)
                    #Log('    Title: ' + curName)
                    #Log('    URL: ' + movieHREF)
                    results.Append(
                        MetadataSearchResult(id=curID,
                                             name=curName,
                                             score=score,
                                             lang=lang))
                count += 1

            if " in " in title.lower() and not content_id:
                try:
                    search_na(results, title, year, lang)
                except (IndexError):
                    pass

            results.Sort('score', descending=True)

    def update(self, metadata, media, lang):
        Log('Data18 Version : ' + VERSION_NO)
        Log('**************UPDATE****************')
        contentURL = EXC_MOVIE_INFO % metadata.id
        html = HTML.ElementFromURL(contentURL)
        metadata.title = parse_document_title(html)

        Log('Current:')
        Log('    Title: ' + metadata.title)
        Log('    ID: ' + metadata.id)
        Log('    Release Date: ' + str(metadata.originally_available_at))
        Log('    Year: ' + str(metadata.year))
        Log('    URL: ' + contentURL)
        for key in metadata.posters.keys():
            Log('    PosterURLs: ' + key)

        # Release Date
        try:
            curdate = parse_document_date(html)
            metadata.originally_available_at = curdate
            # Commenting as not used
            # curyear = str(curdate.year)
            # curmonth = str(curdate.month)
            # curday = str(curdate.day)
            curdate = str(curdate)
            metadata.year = metadata.originally_available_at.year

            '''
            Commenting for now as this replaces the search title with no
            date, which is helpful
            '''
            #metadata.title = re.sub(r'\[\d+-\d+-\d+\]','',metadata.title).strip(' ')

            Log('Title Updated')
            Log('Release Date Sequence Updated')
        except:
            pass

        # Get Poster
        # Get Official Poster if available
        i = 1

        try:
            posterimg = html.xpath(XPATHS['poster-image'])[0]
            posterUrl = posterimg.get('src').strip()
            Log('Official posterUrl: ' + posterUrl)
            metadata.posters[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            i += 1
            Log('Poster Sequence Updated')
        except:
            pass

        # Get First Photo Set Pic if available
        try:
            photoSetIndex = 0
            imageURL = html.xpath(XPATHS['single-image-url'])[photoSetIndex]
            imageURL = imageURL.get('href')
            imagehtml = HTML.ElementFromURL(imageURL)
            posterimg = imagehtml.xpath(XPATHS['single-poster-image'])[0]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.posters[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': imageURL}).content,
                sort_order=i)
            i += 1
            # Random PhotoSet image incase first image isn't desired
            photoSetIndex = random.randint(
                1, len(html.xpath(XPATHS['single-image-url'])) - 1)
            imageURL = html.xpath(XPATHS['single-image-url'])[photoSetIndex]
            imageURL = imageURL.get('href')
            imagehtml = HTML.ElementFromURL(imageURL)
            posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.posters[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': imageURL}).content,
                sort_order=i)
            i += 1
            Log('Poster - Photoset - Sequence Updated')
        except:
            pass

        # Get First Photo Set Pic if available (when src is used instead of
        # href)
        try:
            photoSetIndex = 0
            posterimg = html.xpath(XPATHS['src-single-image'])[photoSetIndex]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.posters[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            i += 1
            # Random PhotoSet image incase first image isn't desired
            photoSetIndex = random.randint(
                1, len(html.xpath(XPATHS['src-single-image'])) - 1)
            posterimg = html.xpath(
                XPATHS['src-single-image'])[photoSetIndex]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.posters[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            i += 1
            Log('Poster - Photoset - Sequence Updated')
        except:
            pass

        # Get alternate Poster - Video
        try:
            posterimg = html.xpath(XPATHS['video-poster'])[0]
            posterUrl = posterimg.get('src').strip()
            Log('Video Postetr Url: ' + posterUrl)
            metadata.posters[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            Log('Video Poster Sequence Updated')
        except:
            pass

        # Get Art
        # Get Art from "Play this Video"
        try:
            i = 1
            posterimg = html.xpath(XPATHS['video-poster'])[0]
            posterUrl = posterimg.get('src').strip()
            Log('ArtUrl: ' + posterUrl)
            metadata.art[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            i += 1
            Log('Art Sequence Updated')
        except:
            pass
        # Second try at "Play this Video" (Embedded html #document)
        try:
            imageURL = html.xpath(XPATHS['video-poster-alternate'])[0]
            imageURL = imageURL.get('src')
            imagehtml = HTML.ElementFromURL(imageURL)
            posterimg = imagehtml.xpath(XPATHS['video-poster'])[0]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.art[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': imageURL}).content,
                sort_order=i)
            i += 1
            Log('Art -Embedded Video- Sequence Updated')
        except:
            pass

     # Get First Photo Set Pic if available
        try:
            photoSetIndex = 0
            imageURL = html.xpath(XPATHS['single-image-url'])[photoSetIndex]
            imageURL = imageURL.get('href')
            imagehtml = HTML.ElementFromURL(imageURL)
            posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.art[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl, headers={'Referer': imageURL}).content, sort_order=i)
            i += 1
            # Random PhotoSet image incase first image isn't desired
            photoSetIndex = random.randint(
                1, len(html.xpath(XPATHS['single-image-url'])) - 1)
            imageURL = html.xpath(XPATHS['single-image-url'])[photoSetIndex]
            imageURL = imageURL.get('href')
            imagehtml = HTML.ElementFromURL(imageURL)
            posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.art[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': imageURL}).content,
                sort_order=i)
            i += 1
            Log('Art - Photoset - Sequence Updated')
        except:
            pass

        # Get First Photo Set Pic if available (when src is used instead of
        # href)
        try:
            photoSetIndex = 0
            posterimg = html.xpath(XPATHS['src-single-image'])[photoSetIndex]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.art[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            i += 1
            # Random PhotoSet image incase first image isn't desired
            photoSetIndex = random.randint(
                1, len(html.xpath(XPATHS['src-single-image'])) - 1)
            posterimg = html.xpath(XPATHS['src-single-image'])[photoSetIndex]
            posterUrl = posterimg.get('src').strip()
            Log('imageUrl: ' + posterUrl)
            metadata.art[posterUrl] = Proxy.Media(
                HTTP.Request(posterUrl,
                             headers={'Referer': contentURL}).content,
                sort_order=i)
            i += 1
            Log('Poster - Photoset - Sequence Updated')
        except:
            pass

        # Genre.
        try:
            metadata.genres.clear()
            genres = html.xpath(XPATHS['genre'])
            if len(genres) > 0:
                for genreLink in genres:
                    genreName = genreLink.text_content().strip('\n')
                    if len(genreName) > 0 and \
                            re.match(r'View Complete List', genreName) is None:
                        if re.match(r'Filter content by multiple tags',
                                    genreName) is None:
                            metadata.genres.add(genreName)
            Log('Genre Sequence Updated')
        except:
            pass

        # Summary.
        try:
            metadata.summary = ""
            paragraph = html.xpath(XPATHS['summary'])[0]
            metadata.summary = paragraph.text_content().replace(
                '&13;', '').strip(' \t\n\r"') + "\n"
            metadata.summary.strip('\n')
            metadata.summary = re.sub(r'Story: \n', '', metadata.summary)
            Log('Summary Sequence Updated')
        except:
            pass

        # Starring
        starring = html.xpath(XPATHS['actor'])
        metadata.roles.clear()
        for member in starring:
            try:
                role = metadata.roles.new()
                role.actor = member.text_content().strip()
                photo = member.get('href').strip()
                # Commenting out as not used
                # photohtml = HTML.ElementFromURL(photo)
                role.photo = html.xpath(
                    '//a[@href="' + photo + '"]//img')[0].get('src')
                Log('Member Photo Url : ' + role.photo)
            except:
                pass
        Log('Starring Sequence Updated')

        # Studio
        try:
            studio = parse_document_studio(html)
            if not studio:
                studio = parse_document_network(html)
                if not studio:
                    studio = parse_document_site(html)

            if studio:
                metadata.studio = studio
                Log('Studio Sequence Updated')
        except:
            pass

        # Collection
        try:
            collection = parse_document_site(html)
            if collection:
                metadata.collections.clear()
                metadata.collections.add(collection)
                Log('Collection Sequence Updated')
        except:
            pass

       # Tagline
        try:
            # html.xpath('//a[@href="http://www.data18.com/sites/"]/following-sibling::a[last()]')[0].get('href')
            metadata.tagline = contentURL
            Log('Tagline Sequence Updated')
        except:
            pass

        # Content Rating
        metadata.content_rating = 'NC-17'

        Log('Updated:')
        Log('    Title:...............' + metadata.title)
        Log('    ID:..................' + metadata.id)
        Log('    Release Date:........' +
            str(metadata.originally_available_at))
        Log('    Year:................' + str(metadata.year))
        Log('    TagLine:.............' + str(metadata.tagline))
        Log('    Studio:..............' + str(metadata.studio))

        try:
            for key in metadata.posters.keys():
                Log('    PosterURLs:..........' + key)
        except:
            pass
        try:
            for key in metadata.art.keys():
                Log('    BackgroundArtURLs:...' + key)
        except:
            pass
        try:
            for x in range(len(metadata.collections)):
                Log('    Network:.............' + metadata.collections[x])
        except:
            pass
        try:
            for x in range(len(metadata.roles)):
                Log('    Starring:............' + metadata.roles[x].actor)
        except:
            pass

        try:
            for x in range(len(metadata.genres)):
                Log('    Genres:..............' + metadata.genres[x])
        except:
            pass
