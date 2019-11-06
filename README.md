XML Processing Tools for FreeMind
===============================================================================
this product includes 2 program.

- fmmulti.py: re-structure freemind xml
- md2fm.py: convert markdown to freemind xml


How to use?
-----------------------------------------
### requirements to a document
- write down requirements to freemind nodes.
- append `doc` attributes to nodes.
- run `fmmulti.py -m doc file` to convert document structure.

### documents to requirements
- write down a document in markdown.
- run `md2fm` to convert to a freemind-xml.
- edit freemind nodes as you want, to realize/sort requirement terms.

```
... freemind to UML (???, underconstruction)
- T.B.D
```


Requirement
-----------------------------------------
- python3 with zipfile support  
    (some linux distros do not include zipfile support at default.)


How to use
-----------------------------------------
```
$ git clone https://github.com/kuri65536/fmmulti.git
$ cd fmmulti
$ python3 fmmulti.py sample.mm -m doc -o sample-d.mm
```


TODO
-----------------------------------------
- ???: convert to uml
- link 1-node:N-nodes for test planning.
- make a freemind plugin.
- link nodes from attributes.
- convert freemind to markdown.
- freemind: save an original structure to output's attributes.
- o markdown: save an original structure to output's attributes. (as `doc` )
- o convert markdown to freemind.


Development Environment
-----------------------------------------

| term | description   |
|:----:|:--------------|
| OS   | Lubuntu 18.04 |
| tool | python 3.6.8  |


License
-----------------------------------------
see the top of source code, it is MPL2.0.


Screenshot
-----------------------------------------
![markdown to freemind](https://gist.githubusercontent.com/kuri65536/4342c39349e744f845d8e7bd223fa919/raw/d26893410ab94b31623a960489f2662c29ec7a69/2019-11-02-145011_549x713_scrot.png)


Releases and Plans
-----------------------------------------

| version | description |
|:-------:|:---|
| 3.0.0   | (under construction) freemind plugin |
| 2.0.0   | (under construction) convert freemind to UML |
| 1.0.0   | (under construction) convert freemind to markdown |
| 0.4.1   | (under construction) tool to convert `backup` attributes to several attributes |
| 0.4.0   | (under construction) save original structure in `backup` attributes |
| 0.3.0 o | restruct freemind by `doc` attributes |
| 0.2.0 o | convert markdown to freemind format |
| 0.1.0 o | start to debug |


Donations
---------------------
If you are feel to nice for this software, please donation to my

- Bitcoin **| 1FTBAUaVdeGG9EPsGMD5j2SW8QHNc5HzjT |**
- Ether **| 0xd7Dc5cd13BD7636664D6bf0Ee8424CFaF6b2FA8f |**
- or librapay, I'm glad from smaller (about $1) and welcome more :D

<!--
vi: ft=markdown:et:fdm=marker
-->
