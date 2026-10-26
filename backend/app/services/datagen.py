"""Reproducible SYNTHETIC Banking & Financial complaint generator with controlled, documented trend spikes.

Everything produced here is synthetic (template-based) and is flagged `is_synthetic=True` in the database.
Labels are noisy on purpose (cross-category sentences, mixed-sentiment closers) so metrics are not trivially 100%.
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd

END_DATE = date(2026, 10, 15)  # fixed so the dataset (and tests) are reproducible

PRODUCTS = {
    "Credit Card": 1.1,
    "Savings Account": 1.0,
    "Home Mortgage": 0.9,
    "Personal Loan": 0.8,
    "UPI & Net Banking": 1.0,
    "Debit Card & ATM": 0.8,
    "Fixed Deposit": 0.6,
    "Student Loan": 0.7,
}

CHANNELS = {
    "Mobile App": 0.30,
    "Net Banking": 0.22,
    "Phone Banking": 0.20,
    "Branch Walk-in": 0.14,
    "Email": 0.10,
    "Ombudsman": 0.04,
}

BASE_MIX = {
    "Unauthorized Fraud": 0.18,
    "Billing & Fees": 0.18,
    "Loan & Mortgage": 0.16,
    "Transaction Failure": 0.16,
    "Account & KYC": 0.12,
    "Credit Reporting": 0.10,
    "Customer Support": 0.06,
    "Other": 0.04,
}

WEEKDAY = [1.15, 1.10, 1.05, 1.0, 0.95, 0.75, 0.70]

CORE = {
    "Unauthorized Fraud": [
        "I noticed an unauthorized charge of $450 on my {p} that I never made.",
        "My {p} was charged by an unknown foreign merchant while the card was in my possession.",
        "Someone cloned my card and withdrew money from an ATM without any OTP or SMS alert.",
        "Multiple fraudulent online transactions occurred on my {p} after my details were compromised.",
        "I reported the stolen {p} immediately, but unauthorized transactions were still cleared by the bank.",
        "An unapproved debit transaction was deducted from my {p} without two-factor authentication.",
        "My {p} details were compromised and fraudulent international purchases were posted.",
        "I received a transaction alert for a cash withdrawal on my {p} that I did not authorize.",
        "A fraudulent merchant charged my {p} three times in the middle of the night.",
        "Money was stolen from my {p} despite never sharing my PIN, OTP, or password with anyone.",
    ],
    "Billing & Fees": [
        "I was charged an overdraft penalty fee even though my {p} maintained the required minimum balance.",
        "My {p} statement shows an unexpected annual maintenance charge that was promised to be waived.",
        "Autopay deducted the monthly bill twice from my {p} this billing cycle.",
        "I was billed a late fee penalty despite submitting the full payment before the due date.",
        "The interest rate applied to my {p} is significantly higher than the rate in my sanction letter.",
        "Unexpected hidden processing charges and finance charges were deducted from my {p}.",
        "My monthly statement includes compounding interest charges on already disputed transactions.",
        "I was overcharged on foreign currency exchange markup fees for my {p}.",
        "The bank deducted an inactive account penalty without giving any prior notification.",
        "A recurring auto-debit charge was billed even after I formally cancelled the mandate on my {p}.",
    ],
    "Loan & Mortgage": [
        "My monthly EMI was debited twice for my {p} this month, causing my balance to go negative.",
        "The loan servicer miscalculated the escrow balance for my property taxes and homeowners insurance.",
        "I applied for an interest rate reduction on my {p} three months ago and have received no response.",
        "The loan payoff statement issued for my {p} includes inaccurate prepayment penalty charges.",
        "My extra principal prepayments were wrongly allocated toward future interest instead of principal reduction.",
        "The interest rate on my floating rate {p} was increased without the mandated regulatory notice.",
        "The bank has not released my original property title deeds even though my {p} is fully paid off.",
        "I was wrongly threatened with foreclosure on my {p} while my loan modification request was under review.",
        "The amortization schedule for my {p} does not reflect my lump sum prepayments.",
        "My mortgage servicer delayed paying the county property tax from my escrow account, resulting in fines.",
    ],
    "Transaction Failure": [
        "The ATM debited $300 from my {p} but no cash was dispensed from the machine.",
        "Money was debited from my {p} via UPI but the beneficiary never received the funds.",
        "The wire transfer from my {p} has been stuck in pending status for over five business days.",
        "The POS terminal payment failed at checkout, but the purchase amount was deducted from my {p}.",
        "IMPS immediate transfer failed with a gateway timeout error and the auto-reversal was not credited.",
        "An online payment was declined by the merchant, yet the funds remain blocked on my {p}.",
        "A cheque deposited in my {p} cleared four days ago, but the funds are still showing on hold.",
        "The NEFT electronic transfer failed due to a bank server error and the funds vanished from my balance.",
        "The cash deposit machine accepted my cash bundle but did not credit my {p} balance.",
        "Card swipe failed due to a network timeout, but my account statement shows duplicate debits.",
    ],
    "Account & KYC": [
        "My net banking login is completely blocked and password reset verification fails repeatedly.",
        "I submitted my updated KYC documents at the branch twice, but my {p} remains frozen.",
        "The mobile banking app crashes every time I try to authenticate with biometric fingerprint or OTP.",
        "I cannot add a new beneficiary to my {p} because the SMS verification code is never delivered.",
        "My account was placed on an administrative debit freeze without prior notice or explanation.",
        "My joint account permissions were altered without authorized signatures or written consent.",
        "I am unable to change my registered mobile number and mailing address on my {p}.",
        "The two-factor authentication token expired and the customer web portal shows a blank screen.",
        "My debit card was deactivated automatically without any replacement card being dispatched.",
        "I have been locked out of my online banking profile for five consecutive days.",
    ],
    "Credit Reporting": [
        "The bank reported an inaccurate 30-day delinquency to Experian and Equifax for a bill paid on time.",
        "An inaccurate settled debt status is still reflecting on my CIBIL credit bureau report.",
        "The credit limit on my {p} was cut drastically without any written justification or notice.",
        "My credit score dropped 65 points due to an erroneous late payment report by your operations team.",
        "A closed {p} is still showing as active with an outstanding balance on my bureau record.",
        "I filed a formal credit bureau dispute 45 days ago, but the bank has not updated the report.",
        "The credit bureau report shows an unauthorized hard inquiry initiated by your loan sales department.",
        "The bank reported me as a defaulter for an account opened fraudulently under my stolen identity.",
    ],
    "Customer Support": [
        "The branch manager was rude, dismissive, and refused to accept my formal dispute letter.",
        "I was transferred between four phone banking representatives and kept on hold for 50 minutes.",
        "The grievance redressal officer closed my complaint ticket without contacting me or resolving it.",
        "The customer service representative gave conflicting and misleading information regarding my dispute.",
        "I visited the branch three times to submit dispute forms and the staff lost my paperwork.",
        "Nobody at phone banking support can provide an update on my escalated dispute ticket.",
    ],
    "Other": [
        "The new cheque book requested 3 weeks ago has not arrived at my registered address.",
        "I requested a physical stamped bank statement for visa verification and it was never delivered.",
        "I need an official balance certificate and interest certificate for income tax filing.",
        "I requested to transfer my {p} to a different local branch and the request is stalled.",
        "The interest rate certificate for income tax deduction contains incorrect account details.",
    ],
}

CLOSERS = {
    "negative": [
        "This is unacceptable and I demand an immediate reversal.",
        "I am escalating this matter to the Banking Ombudsman and Consumer Court.",
        "Fix this immediately or I will close all my accounts with your bank.",
        "Worst banking experience ever, completely unprofessional.",
        "I am not satisfied at all with how this complaint was handled.",
        "This is a disgrace and a complete waste of my time.",
    ],
    "neutral": [
        "Please advise on the next steps to resolve this.",
        "Could you please check your backend logs and investigate?",
        "I would appreciate an urgent update on my ticket.",
        "Kindly let me know how to proceed with the dispute.",
        "Reporting this for your regulatory records and internal audit.",
        "Please confirm receipt of this grievance message.",
    ],
    "positive": [
        "Thank you for the quick help and assistance so far.",
        "I appreciate your team's support and hope it gets sorted quickly.",
        "Good banking service overall, I just need this specific error corrected.",
        "Happy with your branch staff otherwise, thanks in advance.",
        "Not bad service so far, thanks for looking into this.",
        "No complaints about the branch staff, they were very courteous.",
    ],
}

DETAIL = {
    "Unauthorized Fraud": [
        "The transaction took place in another city while I was at work.",
        "I submitted an affidavit of fraud and blocked the card immediately.",
        "The merchant name on the statement is completely unknown to me.",
        "I attached a copy of the police cyber crime complaint report.",
        "No two-factor verification OTP was ever sent to my registered phone.",
    ],
    "Billing & Fees": [
        "I attached the monthly statement highlighting the disputed penalty charge.",
        "The original account agreement clearly stated zero annual maintenance charges.",
        "The transaction timestamp proves the bill was paid 24 hours before the deadline.",
        "My average quarterly balance was well above the required minimum threshold.",
        "The customer care agent previously promised a full waiver on this fee.",
    ],
    "Loan & Mortgage": [
        "The escrow analysis statement contains discrepancies in tax disbursements.",
        "I attached bank transfer receipts confirming timely EMI deductions.",
        "The loan sanction letter guarantees a lower spread on the benchmark rate.",
        "The property insurance premium was deducted twice from my escrow account.",
        "I have written confirmation that all prepayment penalties were waived.",
    ],
    "Transaction Failure": [
        "The ATM terminal number was recorded on the transaction slip.",
        "The UPI transaction reference number (UTR) confirms funds left my account.",
        "The merchant provided written proof that the payment failed at their terminal.",
        "The standard 24-hour auto-reversal SLA has already elapsed.",
        "The beneficiary bank confirmed they never received the inward remittance.",
    ],
    "Account & KYC": [
        "I have submitted self-attested copies of my government ID and address proof.",
        "The branch executive stamped my physical KYC submission receipt.",
        "The error code displayed on screen is AUTH-ERR-403.",
        "I cleared my browser cookies and reinstalled the mobile banking app.",
        "I verified that my registered mobile number and email are active.",
    ],
    "Credit Reporting": [
        "I attached the payment receipt proving zero outstanding balance on that date.",
        "The credit bureau dispute reference ID is still marked as pending bank verification.",
        "The account in question was settled and closed over six months ago.",
        "I have a formal No Objection Certificate (NOC) issued by the bank.",
        "The loan account number mentioned on the bureau report does not belong to me.",
    ],
    "Customer Support": [
        "The call recording will verify the misleading advice given by the representative.",
        "I was given an escalation token number that support claims does not exist.",
        "The branch manager refused to provide an acknowledgment stamp on my dispute letter.",
        "Each representative contradicted what the previous representative told me.",
        "The supervisor refused to come to the phone after a 45-minute hold.",
    ],
    "Other": [
        "I have been an account holder with this bank for over {n} years.",
        "I submitted the signed mandate form at the local branch.",
        "The previous cheque book ran out and I need leaves urgently.",
        "The tracking number provided for the documents shows no movement.",
        "I need this documentation completed before the tax filing deadline.",
    ],
}

ADV = ["extremely", "really", "very", "absolutely", "deeply", "totally"]
ADJ = ["frustrated", "disappointed", "annoyed", "upset", "angry", "fed up"]
CONTEXT = [
    "I have been an account holder for {n} years.",
    "I contacted you by {c} before.",
    "This is the second time this issue has occurred this quarter.",
    "This involves my primary salary account.",
    "It happened again yesterday.",
    "I need this resolved before the weekend.",
]

def make_closer(rng, sent):
    r = rng.random()
    if r < 0.5:
        return rng.choice(CLOSERS[sent])
    if sent == "negative":
        return f"I am {rng.choice(ADV)} {rng.choice(ADJ)} about this."
    if sent == "positive":
        return f"Thanks to {rng.choice(['the branch team', 'your staff', 'the officer', 'everyone'])} for {rng.choice(['the quick reply', 'the help so far', 'the courteous service', 'the patience'])}."
    return f"Could you {rng.choice(['review', 'check', 'investigate', 'look into'])} this {rng.choice(['today', 'soon', 'this week', 'as soon as possible'])}?"

SPIKE_TEXT = {
    "overdraft_batch_glitch": [
        "A core banking system glitch double-charged overdraft penalties across my accounts.",
        "The automated monthly batch run wrongly deducted penalty fees from my {p}.",
        "My account was debited with multiple unauthorized maintenance fees due to a system bug.",
    ],
    "upi_gateway_outage": [
        "The UPI payment server failed and money debited from my {p} was not credited to recipient.",
        "All UPI and IMPS transactions on my {p} are failing with banking network timeout error.",
        "The mobile banking UPI gateway is completely down and transaction amounts are stuck in limbo.",
    ],
    "fraud_card_skimming": [
        "My {p} was compromised in a card skimming attack with unauthorized ATM cash withdrawals.",
        "Multiple fraudulent foreign transactions were charged to my {p} without OTP confirmation.",
        "Unapproved debit card transactions drained funds from my {p} while I still have the card.",
    ],
    "app_login_loop": [
        "Since the version 5.2 mobile banking update, the app is stuck in an authentication loop.",
        "After updating the banking app, biometric login fails and locks my net banking profile.",
        "The latest mobile banking app update keeps crashing with session token expired error.",
    ],
}

def spike_definitions(end: date = END_DATE) -> list[dict]:
    """Ground-truth description of the injected incidents (used by tests and analytical anomaly detection)."""
    return [
        {"name": "overdraft_batch_glitch", "category": "Billing & Fees", "start": end - timedelta(days=200),
         "end": end - timedelta(days=195), "volume_mult": 3.2, "neg_boost": 0.15},
        {"name": "upi_gateway_outage", "category": "Transaction Failure", "start": end - timedelta(days=95),
         "end": end - timedelta(days=90), "volume_mult": 3.5, "neg_boost": 0.15},
        {"name": "fraud_card_skimming", "category": "Unauthorized Fraud", "start": end - timedelta(days=5),
         "end": end, "volume_mult": 3.2, "neg_boost": 0.15},
        {"name": "app_login_loop", "category": "Account & KYC", "start": end - timedelta(days=17),
         "end": end, "volume_mult": 1.9, "neg_boost": 0.1},
        {"name": "support_backlog", "category": "Customer Support", "start": end - timedelta(days=9),
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
                if c == "Unauthorized Fraud":
                    prod_w[prods.index("Credit Card")] *= 2.5
                    prod_w[prods.index("Debit Card & ATM")] *= 2.0
                if c == "Transaction Failure":
                    prod_w[prods.index("UPI & Net Banking")] *= 2.5
                    prod_w[prods.index("Debit Card & ATM")] *= 2.0
                if c == "Loan & Mortgage":
                    prod_w[prods.index("Home Mortgage")] *= 2.5
                    prod_w[prods.index("Personal Loan")] *= 2.0
                p = rng.choice(prods, p=prod_w / prod_w.sum())
                ch = rng.choice(chans, p=cw / cw.sum())
                if sent == "negative" and rng.random() < 0.2:
                    ch = "Ombudsman"

                # core sentence (incident vocabulary replaces it most of the time)
                core = rng.choice(CORE[c])
                for s in active:
                    if s["name"] in SPIKE_TEXT and rng.random() < (0.55 if s["name"] == "app_login_loop" else 0.75):
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
                text = " ".join(parts).format(p=p, n=int(rng.integers(1, 9)), c=ch.lower())
                rows.append((d, text, p, ch, c, sent))

    df = pd.DataFrame(rows, columns=["created_at", "text", "product", "channel", "true_category", "true_sentiment"])
    df = df.sample(frac=1.0, random_state=seed).sort_values("created_at", kind="stable").reset_index(drop=True)
    df.insert(0, "external_id", [f"BNK-{i + 1:06d}" for i in range(len(df))])
    return df
