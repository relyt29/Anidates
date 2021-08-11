# Anidates: The premier dating site for Animetas

This is the code repository for the [Anidates.com](https://anidates.com) website.


# Build Notes

SCSS and JS built using npm (except index.js). `npm run compile` to compile css and js, should place files in static
webserver via flask, sekrets.py needs to be copied or made by hand to webserver





# Nginx

Proxy Pass notes:

```
    location / {
        # First attempt to serve request as file, then
        # as directory, then fall back to displaying a 404.
        proxy_set_header        Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Host $host:$server_port;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_pass http://127.0.0.1:8080;
}
```







