<?xml version="1.0" encoding="utf-8"?>
<!--
  V13. Browser view of the site's two RSS feeds, /news/feed.xml and
  /news/cost-watch/feed.xml. Each feed names this file in an
  <?xml-stylesheet?> line directly after its XML declaration; feed readers
  ignore that line, so the bytes they parse are otherwise unchanged. A browser
  that opens a feed URL runs this transform and shows a readable page instead
  of a raw XML tree.

  XSLT 1.0 only: that is the only version browsers run.

  CSP (src/_headers) is `style-src 'self'; script-src 'self'` on every path,
  including the feeds, and the transformed page inherits it. So the output has
  no <style>, no style="" and no script: the look comes from /css/tokens.css
  and /css/feed.css.

  NO NEW COPY. Everything shown is either the feed's own data (channel title,
  description, link, self URL; item titles, links, dates, descriptions) or a
  label that already exists on the site: "Subscribe by RSS" is the link text on
  /news/ (src/news/index.njk) and /news/cost-watch/ (src/news/cost-watch.njk).

  Descriptions are written with plain xsl:value-of, never
  disable-output-escaping. Both feeds carry plain text in CDATA; value-of
  prints it as text, so any markup that ever reached a description would show
  as literal characters rather than execute. (Firefox does not implement
  disable-output-escaping at all, so it would not render consistently anyway.)
-->
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:atom="http://www.w3.org/2005/Atom"
  exclude-result-prefixes="atom">

  <xsl:output method="html" encoding="utf-8" indent="yes"
    doctype-system="about:legacy-compat"/>

  <xsl:template match="/">
    <xsl:apply-templates select="rss/channel"/>
  </xsl:template>

  <xsl:template match="channel">
    <html lang="{language}">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="title"/></title>
        <link rel="stylesheet" href="/css/tokens.css"/>
        <link rel="stylesheet" href="/css/feed.css"/>
      </head>
      <body>
        <main class="feed">
          <header class="feed-head">
            <h1><xsl:value-of select="title"/></h1>
            <xsl:if test="normalize-space(description)">
              <p class="feed-desc"><xsl:value-of select="description"/></p>
            </xsl:if>
            <xsl:if test="normalize-space(link)">
              <p class="feed-meta"><a href="{link}"><xsl:value-of select="link"/></a></p>
            </xsl:if>
          </header>
          <xsl:if test="atom:link[@rel='self']/@href">
            <section class="feed-sub" aria-labelledby="feed-sub-h">
              <h2 id="feed-sub-h">Subscribe by RSS</h2>
              <p><code class="feed-url"><xsl:value-of select="atom:link[@rel='self']/@href"/></code></p>
            </section>
          </xsl:if>
          <xsl:if test="item">
            <ol class="feed-items">
              <xsl:apply-templates select="item"/>
            </ol>
          </xsl:if>
        </main>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="item">
    <li class="feed-item">
      <xsl:if test="normalize-space(title)">
        <h2>
          <xsl:choose>
            <xsl:when test="normalize-space(link)">
              <a href="{link}"><xsl:value-of select="title"/></a>
            </xsl:when>
            <xsl:otherwise><xsl:value-of select="title"/></xsl:otherwise>
          </xsl:choose>
        </h2>
      </xsl:if>
      <xsl:if test="normalize-space(pubDate)">
        <p class="feed-meta"><xsl:call-template name="rfc822-date">
          <xsl:with-param name="stamp" select="normalize-space(pubDate)"/>
        </xsl:call-template></p>
      </xsl:if>
      <!-- Cost Watch items repeat the title as the description; print it once. -->
      <xsl:if test="normalize-space(description) and normalize-space(description) != normalize-space(title)">
        <p><xsl:value-of select="description"/></p>
      </xsl:if>
    </li>
  </xsl:template>

  <!-- The date part of an RFC-822 stamp, as the feed wrote it:
       "Sat, 01 Aug 2026 09:00:00 +0700" -> "01 Aug 2026". The optional
       day-of-week is dropped and the time and zone are left off; no word is
       added or translated. A stamp without three date tokens is printed
       whole rather than guessed at. -->
  <xsl:template name="rfc822-date">
    <xsl:param name="stamp"/>
    <xsl:variable name="d">
      <xsl:choose>
        <xsl:when test="contains($stamp, ',')">
          <xsl:value-of select="normalize-space(substring-after($stamp, ','))"/>
        </xsl:when>
        <xsl:otherwise><xsl:value-of select="$stamp"/></xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
    <xsl:variable name="day" select="substring-before($d, ' ')"/>
    <xsl:variable name="r1" select="substring-after($d, ' ')"/>
    <xsl:variable name="mon" select="substring-before($r1, ' ')"/>
    <xsl:variable name="r2" select="substring-after($r1, ' ')"/>
    <xsl:variable name="year" select="substring-before(concat($r2, ' '), ' ')"/>
    <xsl:choose>
      <xsl:when test="$day and $mon and $year">
        <xsl:value-of select="concat($day, ' ', $mon, ' ', $year)"/>
      </xsl:when>
      <xsl:otherwise><xsl:value-of select="$stamp"/></xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
