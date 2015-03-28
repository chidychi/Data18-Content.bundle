# Data18-Content
import re
import random

# this code was borrowed from the Excalibur Films Agent. April 9 2013
# URLS
VERSION_NO = '1.2015.03.28.1'
EXC_BASEURL = 'http://www.data18.com/'
EXC_SEARCH_MOVIES = EXC_BASEURL + 'search/?k=%s&t=0'
EXC_MOVIE_INFO = EXC_BASEURL + 'content/%s'

titleFormats = r'DVD|Blu-Ray|BR|Combo|Pack'

def Start():
  HTTP.CacheTime = CACHE_1DAY
  HTTP.SetHeader('User-agent', 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)')


def search_na(results, media_title, year, lang):
  """
  Since N.A. scenes are not appearing in the search we need to do a bit of trickery to get them.
  """
  Log('Alternative search for N.A. websites')
  actors = media_title.split(' in ')[0].split(',')
  actors_url_parts = media_title.split(' in ')[0].lower().replace(' ', '_').split(',')
  na_url_site = media_title.split(' in ',1)[1]
  Log('Search URL: ' + na_url_site)

  # Take the first actor and the website name to search
  query_actor = String.URLEncode(String.StripDiacritics(actors_url_parts[0].replace('-','')))
  searchURL = EXC_BASEURL + query_actor
  Log('Search URL: ' + searchURL)

  try:
    search_results = HTML.ElementFromURL(searchURL)
  except:
    searchURL = EXC_BASEURL + 'dev/' + query_actor
    Log('Search URL: ' + searchURL)
    search_results = HTML.ElementFromURL(searchURL)
  
  xp = '''//select//Option[text()[contains(translate(., "%s", "%s"), "%s")]]//@value''' % (na_url_site.upper(), na_url_site.lower(), na_url_site.lower())
  Log('xPath: ' + xp)
  try:
    try:
      searchURL = search_results.xpath(xp)[0]
    except:
      xp = '''//select//option[text()[contains(translate(., "%s", "%s"), "%s")]]//@value''' % (na_url_site.upper(), na_url_site.lower(), na_url_site.lower())
      Log('xPath: ' + xp)
      searchURL = search_results.xpath(xp)[0]
  except:
    search_results = HTML.ElementFromURL(searchURL + '/sites/')
    xp = '''//a[text()[contains(translate(., "%s", "%s"), "%s")]]//@href''' % (na_url_site.upper(), na_url_site.lower(), na_url_site.lower())
    Log('xPath: ' + xp)
    searchURL = search_results.xpath(xp)[0]
    
  #Log('Search URL: ' + searchURL)
  search_results = HTML.ElementFromURL(searchURL)    	


  #searchURL = EXC_BASEURL + query_actor + '/sites/' + na_url_part + '.html'
  Log('Search URL: ' + searchURL)
  #try:
    #search_results = HTML.ElementFromURL(searchURL)
  #except:
    #searchURL = EXC_BASEURL +'dev/' + query_actor + '/sites/' + na_url_part + '.html'
    #search_results = HTML.ElementFromURL(searchURL)    	
  count = 0
  for movie in search_results.xpath('//div[@class="bscene2 genmed"]//p[@class="line1"]//a[@class="gen11 bold"]'):
    movie_HREF = movie.get("href").strip()
    Log('Movie HREF: ' + movie_HREF)
    current_name = movie.text_content().strip()
    Log('New title: ' + current_name)
    current_ID = movie.get('href').split('/',4)[4]
    Log('New ID: ' + current_ID)
    
    try:
      movieResults = HTML.ElementFromURL(movie_HREF)
      curyear = movieResults.xpath('//p[contains(text(),"Date")]//a')[0].get('href')
      curyear_group = re.search(r'(\d{8})',curyear)
      if curyear_group is None:
        Log('Date: No date found')
        score = 100 - Util.LevenshteinDistance(media_title.lower(), current_name.lower())
        curyear = ''
        curdate = ''
      else:
        curdate = curyear_group.group(0)
        curdate = Datetime.ParseDate(curdate).date()
        curyear = str(curdate.year)
        curmonth = str(curdate.month)
        curday = str(curdate.day)
        curdate = str(curdate)
        Log('Found Date = ' + curdate)
        score = 100 - Util.LevenshteinDistance(media_title.lower(), current_name.lower()) - Util.LevenshteinDistance(year, curyear)
        Log('It Worked ************************************************************')
    except (IndexError):
      score = 100 - Util.LevenshteinDistance(media_title.lower(), current_name.lower())
      curyear = ''
      curdate = ''
      Log('Date: No date found (Exception)')
    if score >= 45:
      if current_name.count(', The'):
        current_name = 'The ' + current_name.replace(', The','',1)
      if curdate:
        current_name = current_name + ' [' + curdate + ']'

      Log('Found:')
      Log('    Date: ' + curdate)
      Log('    ID: ' + current_ID)
      Log('    Title: ' + current_name)
      Log('    URL: ' + movie_HREF)
      results.Append(MetadataSearchResult(id = current_ID, name = current_name, score = score, lang = lang))
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
    try:
        if media.name.isdigit():
            Log('Media.name is numeric')
            contentURL = EXC_MOVIE_INFO % media.name
            html = HTML.ElementFromURL(contentURL)
            title = html.xpath('//div/h1/text()')[0]
            results.Append(MetadataSearchResult(id = media.name, name  = title, score = '100', lang = lang))

    if media.primary_metadata is not None:
      title = media.primary_metadata.title

    year = media.year
    if media.primary_metadata is not None:
      year = media.primary_metadata.year
      Log('Searching for Year: ' + year)

    Log('Searching for Title: ' + title)

    if " in " in title.lower():
      search_na(results, title, year, lang)
      
        
    if len(results) == 0:
      #query = String.URLEncode(String.StripDiacritics(title.replace('-','')))
      query = String.URLEncode(String.StripDiacritics(title))
      
      searchUrl = EXC_SEARCH_MOVIES % query
      Log('search url: ' + searchUrl)
      searchResults = HTML.ElementFromURL(searchUrl)
      searchTitle = searchResults.xpath('//title')[0].text_content()
      count = 0
      for movie in searchResults.xpath('//div[@class="gen"]//p[@class="gen12"]//a[contains(@href,"content")]'):
        movieHREF = movie.get("href").strip()
        Log('MovieHREF: ' + movieHREF)     
        curName = movie.text_content().strip()
        Log('newTitle: ' + curName)
        curID = movie.get('href').split('/',4)[4]
        Log('newID: ' + curID)
        try:
          movieResults = HTML.ElementFromURL(movieHREF)
          curyear = movieResults.xpath('//p[contains(text(),"Date")]//a')[0].get('href')
          curyear_group = re.search(r'(\d{8})',curyear)
          if curyear_group is None:
            Log('Date: No date found')
            score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower())
            curyear = ''
            curdate = ''
          else:
            curdate = curyear_group.group(0)
            curdate = Datetime.ParseDate(curdate).date()
            curyear = str(curdate.year)
            curmonth = str(curdate.month)
            curday = str(curdate.day)
            curdate = str(curdate)
            Log('Found Date = ' + curdate)
            score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower()) - Util.LevenshteinDistance(year, curyear)
            Log('It Worked ************************************************************')
        except (IndexError):
          score = 100 - Util.LevenshteinDistance(title.lower(), curName.lower())
          curyear = ''
          curdate = ''
          Log('Date: No date found (Exception)')
        if score >= 45:
          if curName.count(', The'):
            curName = 'The ' + curName.replace(', The','',1)
          if curdate:
            curName = curName + ' [' + curdate + ']'

          #Log('Found:')
          #Log('    Date: ' + curdate)
          #Log('    ID: ' + curID)
          #Log('    Title: ' + curName)
          #Log('    URL: ' + movieHREF)
          results.Append(MetadataSearchResult(id = curID, name = curName, score = score, lang = lang))
        count += 1
      results.Sort('score', descending=True)

    
    
    

  def update(self, metadata, media, lang):
    Log('Data18 Version : ' + VERSION_NO)
    Log('**************UPDATE****************')
    contentURL = EXC_MOVIE_INFO % metadata.id
    html = HTML.ElementFromURL(contentURL)
    metadata.title = re.sub(titleFormats,'',media.title).strip(' .-+')

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
      curyear = html.xpath('//p[contains(text(),"Date")]//a')[0].get('href')
      curyear_group = re.search(r'(\d{8})',curyear)
      curdate = curyear_group.group(0)
      curdate = Datetime.ParseDate(curdate).date()
      metadata.originally_available_at = curdate
      curyear = str(curdate.year)
      curmonth = str(curdate.month)
      curday = str(curdate.day)
      curdate = str(curdate)
      metadata.year = metadata.originally_available_at.year
      metadata.title = re.sub(r'\[\d+-\d+-\d+\]','',metadata.title).strip(' ')
      Log('Title Updated')
      Log('Release Date Sequence Updated')
    except: pass
    # Get Poster
    # Get Official Poster if available
    i = 1

    try:
      posterimg = html.xpath('//img[@alt="poster"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('Official posterUrl: ' + posterUrl)
      metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content, sort_order = i)
      i += 1
      Log('Poster Sequence Updated')
    except: pass

    # Get First Photo Set Pic if available
    try:
      photoSetIndex = 0
      imageURL =  html.xpath('//img[contains(@alt,"image")]/..')[photoSetIndex].get('href')
      imagehtml = HTML.ElementFromURL(imageURL)
      posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': imageURL}).content, sort_order = i)
      i += 1
      #Random PhotoSet image incase first image isn't desired
      photoSetIndex = random.randint(1,len(html.xpath('//img[contains(@alt,"image")]/..'))-1)
      imageURL =  html.xpath('//img[contains(@alt,"image")]/..')[photoSetIndex].get('href')
      imagehtml = HTML.ElementFromURL(imageURL)
      posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': imageURL}).content, sort_order = i)
      i += 1
      Log('Poster - Photoset - Sequence Updated')
    except: pass

    # Get First Photo Set Pic if available (when src is used instead of href)
    try:
      photoSetIndex = 0
      posterimg = html.xpath('//img[contains(@alt,"image")]')[photoSetIndex]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content, sort_order = i)
      i += 1
      #Random PhotoSet image incase first image isn't desired
      photoSetIndex = random.randint(1,len(html.xpath('//img[contains(@alt,"image")]'))-1)
      posterimg = html.xpath('//img[contains(@alt,"image")]')[photoSetIndex]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content, sort_order = i)
      i += 1
      Log('Poster - Photoset - Sequence Updated')
    except: pass

    # Get alternate Poster - Video
    try:
      posterimg = html.xpath('//img[@alt="Play this Video"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('Video Postetr Url: ' + posterUrl)
      metadata.posters[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content, sort_order = i)
      Log('Video Poster Sequence Updated')
    except: pass

    # Get Art
    # Get Art from "Play this Video"
    try:
      i = 1
      posterimg = html.xpath('//img[@alt="Play this Video"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('ArtUrl: ' + posterUrl)
      metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content,  sort_order = i)
      i += 1
      Log('Art Sequence Updated')
    except: pass
    #Second try at "Play this Video" (Embedded html #document)
    try:
      imageURL =  html.xpath('//*//iframe[contains(@src,"player.php")][1]')[0].get('src')
      imagehtml = HTML.ElementFromURL(imageURL)
      posterimg = imagehtml.xpath('//img[@alt="Play this Video"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': imageURL}).content, sort_order = i)
      i += 1
      Log('Art -Embedded Video- Sequence Updated')
    except: pass

 # Get First Photo Set Pic if available
    try:
      photoSetIndex = 0
      imageURL =  html.xpath('//img[contains(@alt,"image")]/..')[photoSetIndex].get('href')
      imagehtml = HTML.ElementFromURL(imageURL)
      posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': imageURL}).content, sort_order = i)
      i += 1
      #Random PhotoSet image incase first image isn't desired
      photoSetIndex = random.randint(1,len(html.xpath('//img[contains(@alt,"image")]/..'))-1)
      imageURL =  html.xpath('//img[contains(@alt,"image")]/..')[photoSetIndex].get('href')
      imagehtml = HTML.ElementFromURL(imageURL)
      posterimg = imagehtml.xpath('//img[@alt= "image"]')[0]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': imageURL}).content, sort_order = i)
      i += 1
      Log('Art - Photoset - Sequence Updated')
    except: pass

    # Get First Photo Set Pic if available (when src is used instead of href)
    try:
      photoSetIndex = 0
      posterimg = html.xpath('//img[contains(@alt,"image")]')[photoSetIndex]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content, sort_order = i)
      i += 1
      #Random PhotoSet image incase first image isn't desired
      photoSetIndex = random.randint(1,len(html.xpath('//img[contains(@alt,"image")]'))-1)
      posterimg = html.xpath('//img[contains(@alt,"image")]')[photoSetIndex]
      posterUrl = posterimg.get('src').strip()
      Log('imageUrl: ' + posterUrl)
      metadata.art[posterUrl] = Proxy.Media(HTTP.Request(posterUrl, headers={'Referer': contentURL}).content, sort_order = i)
      i += 1
      Log('Poster - Photoset - Sequence Updated')
    except: pass

    # Genre.
    try:
      metadata.genres.clear()
      genres = html.xpath('//*[b[contains(text(),"Categories")]]//a[contains(@href, ".html")]')
      if len(genres) > 0:
        for genreLink in genres:
          genreName = genreLink.text_content().strip('\n')
          if len(genreName) > 0 and re.match(r'View Complete List', genreName) is None:
            if re.match(r'Filter content by multiple tags', genreName) is None:
              metadata.genres.add(genreName)
      Log('Genre Sequence Updated')
    except: pass

    # Summary.
    try:
      metadata.summary = ""
      paragraph = html.xpath('//*[b[contains(text(),"Story:")]]')[0]
      metadata.summary = paragraph.text_content().replace('&13;', '').strip(' \t\n\r"') + "\n\n"
      metadata.summary.strip('\n')
      metadata.summary = re.sub(r'Story:','',metadata.summary)
      Log('Summary Sequence Updated')
    except: pass

    # Starring
    starring = html.xpath('//*[b[contains(text(),"Starring:")]]//a[@class="bold"]')
    metadata.roles.clear()
    for member in starring:
      try:
        role = metadata.roles.new()
        role.actor = member.text_content().strip()
        photo = member.get('href').strip()
        photohtml = HTML.ElementFromURL(photo)
        role.photo = html.xpath('//a[@href="' + photo + '"]//img')[0].get('src')
        Log('Member Photo Url : ' + role.photo)
      except: pass
    Log('Starring Sequence Updated')

    # Studio
    try:
      metadata.studio = html.xpath('//a[@href="http://www.data18.com/sites/"]/following-sibling::a')[0].text_content().strip()
      Log('Studio Sequence Updated')
    except: pass

    # Collection
    try:
      collection = html.xpath('//a[@href="http://www.data18.com/sites/"]/following-sibling::a')[1].text_content().strip()
      metadata.collections.clear ()
      metadata.collections.add (collection)
      Log('Collection Sequence Updated')
    except: pass

   # Tagline
    try:
      metadata.tagline = contentURL #html.xpath('//a[@href="http://www.data18.com/sites/"]/following-sibling::a[last()]')[0].get('href')
      Log('Tagline Sequence Updated')
    except: pass


    Log('Updated:')
    Log('    Title:...............' + metadata.title)
    Log('    ID:..................' + metadata.id)
    Log('    Release Date:........' + str(metadata.originally_available_at))
    Log('    Year:................' + str(metadata.year))
    Log('    TagLine:.............' + str(metadata.tagline))
    Log('    Studio:..............' + str(metadata.studio))

    try:
      for key in metadata.posters.keys():
        Log('    PosterURLs:..........' + key)
    except: pass
    try:
      for key in metadata.art.keys():
        Log('    BackgroundArtURLs:...' + key)
    except: pass
    try:
      for x in range (len(metadata.collections)):
        Log('    Network:.............' + metadata.collections[x])
    except: pass
    try:
      for x in range (len(metadata.roles)):
        Log('    Starring:............' + metadata.roles[x])
    except: pass

    try:
      for x in range (len(metadata.genres)):
        Log('    Genres:..............' + metadata.genres[x])
    except: pass
