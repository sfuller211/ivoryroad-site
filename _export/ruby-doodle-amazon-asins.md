# Ruby Doodle Amazon ASINs

Pulled from the Shopify `custom.amazon_link` metafield on each product, then each
`amzn.to` short link was followed to its final destination and the ASIN read off it.
Every one of the ten was then verified by matching the live Amazon page title.

| Book | Shopify short link | ASIN | Direct link |
|---|---|---|---|
| The Pickup Truck | amzn.to/3GQGMYk | B0CQF5PRPP | https://www.amazon.com/dp/B0CQF5PRPP |
| Classic Cars Around the World | amzn.to/3Q8QGcm | B0CGT64CRZ | https://www.amazon.com/dp/B0CGT64CRZ |
| Falling Leaves and Cozy Scenes | amzn.to/3s1WJHF | B0CLP5YYTG | https://www.amazon.com/dp/B0CLP5YYTG |
| Bold Blooms | amzn.to/45EpYQf | B0D7N4PP5H | https://www.amazon.com/dp/B0D7N4PP5H |
| Winter Fun | amzn.to/46ZYRhR | B0CJXDSJQJ | https://www.amazon.com/dp/B0CJXDSJQJ |
| Toddlers Animal | amzn.to/494DvBP | B0CJXGYFCV | https://www.amazon.com/dp/B0CJXGYFCV |
| Animal Kingdom Adventures | amzn.to/473qg2l | B0CJXDRWDQ | https://www.amazon.com/dp/B0CJXDRWDQ |
| Tale of Two | amzn.to/3ukfjvy | B0CTHJZFH2 | https://www.amazon.com/dp/B0CTHJZFH2 |
| Cozy Country Charm | amzn.to/4dfMscf | B0DFY1L76J | https://www.amazon.com/dp/B0DFY1L76J |
| Enchanted Realms | (Shopify link is wrong) | B0CP2V93L2 | https://www.amazon.com/dp/B0CP2V93L2 |

## Data bug in Shopify, still unfixed there

**Enchanted Realms and The Pickup Truck share the same `amzn.to/3GQGMYk` link in
Shopify,** and it resolves to The Pickup Truck. So the Enchanted Realms product page on
ivoryroad.shop is sending print buyers to the wrong book right now.

The correct one is **B0CP2V93L2**, confirmed by the live Amazon page title:
"Enchanted Realms: Medieval Castles, Knights and Dragons - A Coloring Odyssey",
by Doodle, Ruby, ISBN 9798869932242.

To fix it on the current store: edit the Enchanted Realms product in Shopify and set
`custom.amazon_link` to `https://www.amazon.com/dp/B0CP2V93L2`.

Note the title on Amazon reads "A Coloring Odyssey" while the Shopify product says
"A Coloring Journey". Same book, but worth making the two match.
