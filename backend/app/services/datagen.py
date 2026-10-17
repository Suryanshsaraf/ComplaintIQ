"""Reproducible SYNTHETIC complaint generator with controlled, documented trend spikes.

Everything produced here is synthetic (template-based) and is flagged `is_synthetic=True` in the database.
Labels are noisy on purpose (cross-category sentences, mixed-sentiment closers) so metrics are not trivially 100%.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

END_DATE = date(2026, 10, 15)  # fixed so the dataset (and tests) are reproducible

PRODUCTS = {"Smartphone": 1.0, "Laptop": 0.8, "Wireless Earbuds": 0.9, "Smart Watch": 0.7, "Home Router": 0.7,
            "Streaming Subscription": 1.1, "Fitness Tracker": 0.6, "Smart Speaker": 0.6}
CHANNELS = {"Email": 0.28, "Phone": 0.2, "Web Form": 0.18, "Chat": 0.16, "Social Media": 0.12, "App Store": 0.06}
BASE_MIX = {"Billing": .17, "Delivery": .19, "Product Quality": .17, "Technical Support": .14, "Refunds": .10,
            "Account Issues": .09, "Customer Service": .09, "Other": .05}
WEEKDAY = [1.15, 1.10, 1.05, 1.0, 0.95, 0.75, 0.70]

CORE = {
    "Billing": [
        "I was charged twice for my {p} this month.", "My invoice shows an incorrect amount for the {p}.",
        "There is an unexpected fee on my bill that nobody explained.",
        "The price I was quoted for the {p} does not match what I was billed.",
        "My credit card was charged after I cancelled my plan.",
        "I received a late payment penalty even though I paid on time.", "The tax on my invoice looks wrong.",
        "Autopay took money from my bank account on the wrong date.",
        "My monthly statement includes charges I do not recognize.", "I was overcharged on my last {p} payment."],
    "Delivery": [
        "My {p} order has not arrived and the tracking has not updated in days.",
        "The package was delivered to the wrong address.",
        "Delivery was supposed to take 3 days but it has been two weeks.",
        "The courier left my {p} outside in the rain and it got damaged.",
        "I was told the order shipped but there is no tracking number.",
        "The delivery driver never showed up for my scheduled slot.", "My parcel arrived with the box crushed.",
        "Items from my {p} order were missing from the shipment.", "Shipping is far slower than promised.",
        "The carrier marked my order as delivered but I never received it."],
    "Product Quality": [
        "The {p} stopped working after just two weeks.", "The {p} arrived with a cracked screen and scratches.",
        "The material feels cheap and started falling apart.", "The {p} is defective and makes a loud buzzing noise.",
        "The battery on my {p} drains within an hour.", "The stitching came loose on first use.",
        "The {p} overheats and shuts down randomly.", "The color looks nothing like the pictures and the build is flimsy.",
        "Parts of the {p} were broken out of the box.", "The quality has gone downhill compared to my previous {p}."],
    "Technical Support": [
        "I cannot connect my {p} to the app, it keeps showing an error.",
        "The software crashes every time I open the settings page.",
        "The firmware update failed and my {p} is stuck on a loading screen.",
        "I have been unable to pair the device over bluetooth.",
        "The troubleshooting steps from your guide did not fix the problem.",
        "The app freezes on startup after the latest update.", "I need help configuring the wifi setup on my {p}.",
        "The support portal gives a timeout error when I submit a ticket.",
        "The sync between my devices keeps failing.", "The installation wizard stops at 40 percent with an error code."],
    "Refunds": [
        "I returned the {p} three weeks ago and still have not received my refund.",
        "I was promised a full refund but only got store credit.",
        "My refund was approved but the money never reached my account.",
        "The return label you sent does not work so I cannot send back the {p}.",
        "I requested a refund for the defective {p} and was denied.",
        "Refund processing is taking much longer than the stated five business days.",
        "I was only refunded part of the amount I paid.", "Nobody has confirmed my return for the {p}.",
        "I cancelled within the trial period but you refuse to refund me.", "The refund went to the wrong card."],
    "Account Issues": [
        "I cannot log in to my account, the password reset email never arrives.",
        "My account was locked without any explanation.", "I was unable to update my email address on my profile.",
        "Someone changed my account details and I did not authorize it.",
        "The two factor authentication code is never delivered to my phone.",
        "My account shows the wrong subscription tier.", "I cannot delete my account as the button does nothing.",
        "My profile data disappeared after I signed in.", "I keep getting logged out of my account every few minutes.",
        "My loyalty points vanished from my account."],
    "Customer Service": [
        "The agent I spoke to was rude and dismissive.", "I have been on hold for over an hour with no answer.",
        "Nobody replied to my emails for a week.",
        "I was transferred between three departments and had to repeat myself every time.",
        "The chat representative closed the conversation without solving anything.",
        "The support staff gave me conflicting information.", "No one called me back as promised.",
        "The store employee ignored me when I asked for help with the {p}.",
        "Your representative promised a follow up that never happened.",
        "Customer service has been unhelpful and slow to respond."],
    "Other": [
        "The website layout is confusing and hard to navigate.", "I would like to suggest adding more payment options.",
        "Your store was closed during the posted opening hours.", "The newsletter emails are too frequent.",
        "The packaging uses too much plastic.", "Please offer the {p} in more colors.",
        "I could not find the product information I was looking for.", "The mobile site is slow on my phone.",
        "The promotional offer details were unclear.", "Your loyalty program rules are hard to understand."],
}

CLOSERS = {
    "negative": ["This is unacceptable.", "I am extremely frustrated.", "Very disappointed with this experience.",
                 "Terrible, I want this fixed immediately.", "I am furious and considering leaving.",
                 "Worst experience ever.", "I am not satisfied at all.", "I am not happy with how this was handled.",
                 "This is a disgrace and a waste of my time."],
    "neutral": ["Please advise on next steps.", "Could you look into this?", "I would like an update.",
                "Kindly let me know how to proceed.", "Reporting this for your records.",
                "Let me know what information you need.", "Please confirm receipt of this message."],
    "positive": ["Thank you for the quick help so far.", "I appreciate your team and hope it gets sorted.",
                 "Great service overall, I just need this resolved.", "Happy with the brand otherwise, thanks in advance.",
                 "Not bad service so far, thanks.", "No complaints about the staff, they were lovely."],
}
DETAIL = {
    "Billing": ["The amount differs from the confirmation email.", "I attached the statement for reference.",
                "The charge appeared on the billing page of my account.", "My payment was made by visa card.",
                "The invoice number is printed on the second page."],
    "Delivery": ["The tracking page still says in transit.", "The shipping address on the label looks correct.",
                 "The estimated arrival date keeps changing.", "I paid extra for express shipping.",
                 "A neighbour said no courier had visited the street."],
    "Product Quality": ["I only used it a handful of times.", "The warranty card is still in the box.",
                        "There is visible damage near the edge.", "My previous model lasted for years.",
                        "The finish is peeling off in places."],
    "Technical Support": ["I already restarted the device twice.", "The error code displayed is unclear.",
                          "I tried reinstalling the application.", "The status light keeps blinking orange.",
                          "The manual does not explain this situation."],
    "Refunds": ["The return was posted over two weeks ago.", "I kept the receipt and the original packaging.",
                "The bank shows no pending credit.", "The return confirmation email arrived last month.",
                "I selected the original payment method for the reimbursement."],
    "Account Issues": ["I use the same email address as always.", "The verification link expired immediately.",
                       "My username is no longer recognised.", "The profile page loads but shows no data.",
                       "I cleared my browser cache without any change."],
    "Customer Service": ["The call lasted nearly forty minutes.", "I was given a reference number but nobody uses it.",
                         "Each agent asked me the same questions again.", "The email thread has no reply from your side.",
                         "The manager on duty was unavailable."],
    "Other": ["I am writing about a general matter.", "This is feedback rather than an urgent request.",
              "I have used the site on several different browsers.", "A friend had the same impression.",
              "I hope this can be considered for the future."],
}
ADV = ["extremely", "really", "very", "absolutely", "deeply", "totally"]
ADJ = ["frustrated", "disappointed", "annoyed", "upset", "angry", "fed up"]
CONTEXT = ["I have been a customer for {n} years.", "I contacted you by {c} before.", "This is the second time this has happened.",
           "I ordered this as a gift.", "It happened again yesterday.", "I need this resolved before the weekend."]

# vocabulary used by the injected incidents (so topic / emerging-term detection has something real to find)
def make_closer(rng, sent):
    r = rng.random()
    if r < 0.5:
        return rng.choice(CLOSERS[sent])
    if sent == "negative":
        return f"I am {rng.choice(ADV)} {rng.choice(ADJ)} about this."
    if sent == "positive":
        return f"Thanks to {rng.choice(['the team', 'your staff', 'the agent', 'everyone'])} for "                f"{rng.choice(['the quick reply', 'the help so far', 'the friendly service', 'the patience'])}."
    return f"Could you {rng.choice(['review', 'check', 'investigate', 'look into'])} this "            f"{rng.choice(['today', 'soon', 'this week', 'as soon as possible'])}?"


SPIKE_TEXT = {
    "billing_incident": ["A system error on your side charged me twice on the same day.",
                         "The duplicate charge from the billing glitch is still on my statement."],
    "delivery_incident": ["The logistics partner seems overwhelmed and my {p} is stuck at a depot.",
                          "There is a huge carrier backlog and my {p} order has not moved."],
    "delivery_recent": ["The carrier backlog at the regional warehouse has delayed my {p} for over a week.",
                        "My {p} is stuck at the warehouse because of the carrier backlog."],
    "app_update": ["Since the version 5.2 update the app is stuck in a login loop.",
                   "After updating to version 5.2 the dashboard shows a blank screen.",
                   "The latest app update keeps logging me out with a token expired error."],
}


def spike_definitions(end: date = END_DATE) -> list[dict]:
    """Ground-truth description of the injected incidents (used by tests and the README)."""
    return [
        {"name": "billing_incident", "category": "Billing", "start": end - timedelta(days=200),
         "end": end - timedelta(days=195), "volume_mult": 3.2, "neg_boost": 0.15},
        {"name": "delivery_incident", "category": "Delivery", "start": end - timedelta(days=95),
         "end": end - timedelta(days=90), "volume_mult": 3.5, "neg_boost": 0.15},
        {"name": "delivery_recent", "category": "Delivery", "start": end - timedelta(days=5),
         "end": end, "volume_mult": 3.2, "neg_boost": 0.15},
        {"name": "app_update", "category": "Technical Support", "start": end - timedelta(days=17),
         "end": end, "volume_mult": 1.9, "neg_boost": 0.1},
        {"name": "service_sentiment_drop", "category": "Customer Service", "start": end - timedelta(days=9),
         "end": end, "volume_mult": 1.8, "neg_boost": 0.30},
    ]


def generate(n_rows: int = 7000, seed: int = 42, end: date = END_DATE, days: int = 365) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    spikes = spike_definitions(end)
    start = end - timedelta(days=days - 1)
    cats = list(BASE_MIX)
    prods, pw = list(PRODUCTS), np.array(list(PRODUCTS.values()))
    chans, cw = list(CHANNELS), np.array(list(CHANNELS.values()))

    # expected volume per (day, category)
    day_list = [start + timedelta(days=i) for i in range(days)]
    mean = np.zeros((days, len(cats)))
    for i, d in enumerate(day_list):
        trend = 0.85 + 0.30 * i / days
        for j, c in enumerate(cats):
            m = BASE_MIX[c] * WEEKDAY[d.weekday()] * trend
            for s in spikes:
                if s["category"] == c and s["start"] <= d <= s["end"]:
                    m *= s["volume_mult"]
            mean[i, j] = m
    # scale baseline so the total is close to n_rows
    mean *= n_rows / mean.sum()
    counts = rng.poisson(mean)

    rows = []
    for i, d in enumerate(day_list):
        for j, c in enumerate(cats):
            active = [s for s in spikes if s["category"] == c and s["start"] <= d <= s["end"]]
            for _ in range(counts[i, j]):
                neg_boost = sum(s["neg_boost"] for s in active)
                pn = min(0.95, 0.66 + neg_boost)
                rest = 1 - pn
                sent = rng.choice(["negative", "neutral", "positive"], p=[pn, rest * 0.68, rest * 0.32])
                prod_w = pw.copy()
                if c in ("Billing", "Refunds"):
                    prod_w[prods.index("Streaming Subscription")] *= 2.5
                if c == "Technical Support":
                    prod_w[prods.index("Home Router")] *= 2.0
                    prod_w[prods.index("Smart Watch")] *= 1.5
                p = rng.choice(prods, p=prod_w / prod_w.sum())
                ch = rng.choice(chans, p=cw / cw.sum())
                if sent == "negative" and rng.random() < 0.2:
                    ch = "Social Media"

                # core sentence (incident vocabulary replaces it most of the time)
                core = rng.choice(CORE[c])
                for s in active:
                    if s["name"] in SPIKE_TEXT and rng.random() < (0.55 if s["name"] == "app_update" else 0.75):
                        core = rng.choice(SPIKE_TEXT[s["name"]])
                parts = [core]
                if rng.random() < 0.10:  # cross-category sentence -> realistic label ambiguity
                    other = rng.choice([x for x in cats if x != c])
                    parts.append(rng.choice(CORE[other]))
                if rng.random() < 0.55:
                    parts.append(rng.choice(DETAIL[c]))
                if rng.random() < 0.35:
                    parts.append(rng.choice(CONTEXT))
                if rng.random() < 0.7:
                    closer_sent = sent if rng.random() > 0.10 else rng.choice(["negative", "neutral", "positive"])
                    parts.append(make_closer(rng, closer_sent))
                text = " ".join(parts).format(p=p.lower(), n=int(rng.integers(1, 9)), c=ch.lower())
                rows.append((d, text, p, ch, c, sent))

    df = pd.DataFrame(rows, columns=["created_at", "text", "product", "channel", "true_category", "true_sentiment"])
    df = df.sample(frac=1.0, random_state=seed).sort_values("created_at", kind="stable").reset_index(drop=True)
    df.insert(0, "external_id", [f"SYN-{i + 1:06d}" for i in range(len(df))])
    return df
