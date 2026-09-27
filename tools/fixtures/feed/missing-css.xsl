<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom" exclude-result-prefixes="atom">
  <xsl:output method="html" encoding="utf-8" doctype-system="about:legacy-compat"/>
  <xsl:template match="/">
    <html lang="en"><head><title><xsl:value-of select="rss/channel/title"/></title>
    <link rel="stylesheet" href="/css/not-there.css"/></head>
    <body><h1><xsl:value-of select="rss/channel/title"/></h1>
    <p><code><xsl:value-of select="rss/channel/atom:link[@rel='self']/@href"/></code></p>
    <ol><xsl:for-each select="rss/channel/item"><li>
      <h2><xsl:value-of select="title"/></h2>
      <p><xsl:value-of select="description"/></p>
    </li></xsl:for-each></ol>
    </body></html>
  </xsl:template>
</xsl:stylesheet>
