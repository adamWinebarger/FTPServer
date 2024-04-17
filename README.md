# FTPServer

### Basically just kicking this thing onto github so I can use it between my Linux box and my Mac

## Important notes

- So I've been using a statement in python on the server-side file that tells me the IP address that the server is running on in order to test my program across two different machines; and while it works as intended on my linux box (running python 3.12.3), my macbook refuses to run the server file because of that command specifically (of course, I just noticed that my macbook is running python 3.11.7. So that might have something to do with it)
- Also, the server crashes when I send it SIGINT and it won't even shut down if there are still clients connected - that's good... I guess? But it's something worth noting if the server refuses to exit.