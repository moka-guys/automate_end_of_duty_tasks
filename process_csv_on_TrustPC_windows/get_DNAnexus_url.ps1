# Works like wget, pass URLs to script to download them 
# dl_urls.ps1 url [url path]
Import-Module BitsTransfer
$url = $args[0] 
$path = $args[1]
Start-BitsTransfer -Source $url -Destination $path