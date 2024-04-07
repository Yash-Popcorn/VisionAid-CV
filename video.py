import requests

def suggest_youtube_videos(query):
    API_KEY = 'AIzaSyDo-1hDtAFqHGDK-aVCpjWhCB6VFiwh_N8'
    BASE_URL = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'key': API_KEY,
        'maxResults': 5  # Number of videos to suggest
    }
    response = requests.get(BASE_URL, params=params)
    if response.status_code == 200:
        videos = response.json()['items']
        suggestions = []
        for video in videos:
            title = video['snippet']['title']
            video_id = video['id']['videoId']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            suggestions.append(video_url)
        return suggestions
    else:
        print('Failed to fetch YouTube videos')
        return []

""""
# Example usage:
query = 'Minecraft Videos'
video_suggestions = suggest_youtube_videos(query)
if video_suggestions:
    for video in video_suggestions:
        print(f'Title: {video["title"]}\nURL: {video["url"]}\n')
"""""

