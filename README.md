
# Cachecat

**Cachecat** is a proof of concept demonstrating [Web Cache Tunneling](https://www.boozallen.com/insights/cyber/tech/introducing-web-cache-tunneling.html), the utilization of a public web cache as shared key-value storage through cache poisoning. All demonstrations use the deliberately vulnerable page, [https://webcachetunneling.com](https://webcachetunneling.com/).

## Requirements

- python>=3.5
- python3-pip

## Install

```
git clone https://github.com/boozallen-darklabs/cachecat
pip3 install -e ./cachecat
```

## Demonstration

- [Storing arbitrary data in a public web cache](https://asciinema.org/a/5yZcbSk8VKGJf0UITSsjnKbcA)
- [Uploading and downloading a file from a public web cache](https://asciinema.org/a/0krGSneBOMK6htuwVFZT0B78D)
- [Bidirectional communication over a public web cache](https://asciinema.org/a/xc3FKMFipWXFnY7JnAdNyie0s)
- [Tunneling a VPN over a public web cache](https://asciinema.org/a/Gx9TsNMYKqKZsby4VSE8YEy9t)

For more details, please refer to the [publication](https://www.boozallen.com/insights/cyber/tech/introducing-web-cache-tunneling.html) or [documentation](https://boozallen-darklabs.github.io/cachecat/build/html/).
