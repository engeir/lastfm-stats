# Eirik's Lastfm

## Install

<!-- x-release-please-start-version -->

```bash
docker pull ghcr.io/engeir/lastfm-stats
docker run --env-file .env -it --rm -p 3000:3000 -p 8000:8000 --detach --name lastfm-stats ghcr.io/engeir/lastfm-stats:v0.3.7
```

<!-- x-release-please-end -->

## More

See:

- <https://geoffboeing.com/2016/05/analyzing-lastfm-history/>
- <https://m-w-bochniewicz.medium.com/music-analysis-with-python-part-1-create-your-own-dataset-with-lastfm-and-spotify-8223a46fad4b>
- <https://hemisferios.chmedina.com/using-the-last-fm-api-to-extract-data-and-analyzing-it-with-python-part-2-fa1a8e74cd26>
- <https://www.dataquest.io/blog/last-fm-api-python/>
- [Icons](https://lucide.dev/)
