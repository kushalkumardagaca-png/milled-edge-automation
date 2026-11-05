# Installing the MILLED EDGE Market Today theme

The Blogger XML is a complete theme based on the current MILLED EDGE theme. It contains the Market Today menu, direct links to published category posts, the commodity price board, the homepage tapes, and the 18-division directory.

1. In Blogger, open **Theme** and back up the current theme.
2. Use **Restore / Upload** to upload `theme-104-category-homepage.xml`.
3. On desktop, click **Market Today**. The 18 divisions should open between the two navigation rows in a six-column grid. Hover or click a division to reveal its published categories. A category link opens its post directly; the four unpublished categories are marked pending, not linked to an archive.
4. The **Commodities** tile opens one flat commodity price board. It does not list commodity subcategories, futures, ETFs, miners, or other related securities. The board shows only ten provider-supported commodity CFD references (including gold and silver), with quote units and a disclosure that CFD references are not local physical/retail cash prices. Indicative INR per gram is a reference conversion only.
5. The homepage quote feeds refresh approximately every 60 seconds. Coverage and timing vary by instrument and exchange; no value is fabricated when the provider returns none.

## Separate post-body update

The updated category-post source has a rebuilt global search (bounded provider requests, explicit timeout/failure feedback, no misleading generic “Submitted” status) and tighter small-screen layout rules. Those are post-body changes, so uploading the theme XML alone does not update already-published post bodies. The repository workflow is configured to patch the 100 existing public posts after its write-limit cooldown; it uses the original Blogger publication timestamps and an existing-only guard, so it will not create the four pending entries. The regenerated HTML for all 104 catalog entries is in `content/market-posts/`.

`content/market-post-links.json` maps the 100 currently published category posts to their canonical Blogger URLs. The commodity-category URLs are no longer presented in the division menus; the theme routes those legacy URLs to the single commodity board.
