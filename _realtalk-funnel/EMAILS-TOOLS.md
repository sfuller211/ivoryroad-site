# Real Talk Tools — teen sequence
Six emails. Written to the teen guy, not to his parent. This is the second campaign and it is separate from the Hearts and Home sequence.

Trigger: added to the **Real Talk Tools** group. Delays: 0, 2, 4, 7, 10, 14 days. Same spacing as Hearts and Home on purpose, so there is one system to run and not two.

---

## SETUP — what is built and what is left

**Built Sep 25 2026.** There is no separate teen page. The Real Talk Tools box sits on the one landing page, under the Hearts & Home box and above the four-books image, with its own form.

- `landing.html` now has two cards and two `sender-form-field` divs. `{{SENDER_FORM_ID}}` is Hearts and Home, `{{TOOLS_FORM_ID}}` is this one.
- The Source attribution script was filling only the FIRST form's hidden Source field. With two forms that would have left this one visible and empty on every landing path, which is the bug the script exists to prevent. It now fills every source field on the page and runs one observer per document instead of one per field.
- `/rt/tools-thanks/` is the confirmation page, separate from `/rt/thanks/`, because the two deliver different files.
- `/tools` is unchanged: still a 301 to the PDF.

**Left to do, and it needs a Sender login.**

1. **Create the group.** Sender > Subscribers > Groups, called `Real Talk Tools`.
2. **Create the form.** A second form, separate from `erkw82`. Email field only, no first name, since none of these emails use one. Add the hidden Source field the same way the Hearts and Home form has it, or the channel is lost for everyone who signs up through this box. Post-submit redirect to `https://ivoryroad.shop/rt/tools-thanks/`.
3. **Put the form id in build.py.** `TOOLS_FORM_ID = ""` near the top. Until it is filled the box renders with no form in it and the build prints a warning.
4. **Build the automation** on the Real Talk Tools group, delays 0, 2, 4, 7, 10, 14.

**Overlap is intended.** Someone who fills in both boxes lands on both lists and gets both sequences. They are teaching two different guides to two different readers, so they do not repeat each other.

## Voice rules for this sequence

Different reader, so some rules change.

- **Shorter than the parent emails. Much shorter.** He is reading this on a phone, standing up, with about fifteen seconds of patience. Sixty to a hundred words per email.
- **No teen slang.** Scott is an adult and should sound like one. Trying to sound fifteen is the fastest way to lose a fifteen year old.
- **Never guilt him for not doing it.** No "did you try it yet." He gets enough of that.
- **Do not ask him to reply.** He will not, and an unanswered ask trains him to ignore the rest.
- **Faith plainly, never as a sermon.** It shows up the way it shows up in the book.
- **No first name.** The teen form may not even collect one, and a name at the top of an email is what adults do when they want something.
- No em dashes. Same as everything else.

Each email maps to one page of the Tools pack, so the sequence teaches the thing he already downloaded instead of selling something new.

---

## Email 1 — Immediately
**Subject:** Your Real Talk Tools
**Preview text:** Print it or don't, it's yours

Here it is.

[Download Real Talk Tools] &rarr; `ivoryroad.shop/tools`

Five pages. A check-in page, some small things to try, a page about labels, one-sentence prayers, and scripture cards you can cut out.

You don't have to do all of it. You don't have to do any of it today.

Start with page one. It takes about two minutes and nobody is grading it.

One note if you're a parent who grabbed this for your son. Print it and leave it somewhere he'll come across it. I wouldn't walk him through it, because it works better when it's his. Everything after this email is written to him, so hand it over or just read along.

Scott
Real Talk &middot; ivoryroad.shop

---

## Email 2 — Day 2
**Subject:** How are you, really
**Preview text:** Not the version you say at dinner

Somebody asks how you're doing and you say good.

Not because you're lying. It's just faster.

And most of the time they weren't really asking. They were saying hi.

The check-in page is the version you don't have to say out loud. Tired. Stressed. Numb. Hopeful. Circle whatever's true. Nobody sees it.

It sounds too simple to matter. It isn't. Most guys have never put a word on it, and putting a word on it is most of the work.

Scott
Real Talk &middot; ivoryroad.shop

---

## Email 3 — Day 4
**Subject:** Without making it a big deal
**Preview text:** Five small things

The problem with opening up is that it sounds like a whole event. Sitting down. Eye contact. Somebody asking follow-up questions.

That's not the only version of it.

There's a page in your pack with five small ones. Answer one honest question at dinner. Text somebody you trust one real sentence. Say "I had a hard day" and don't explain it.

That last one is where I'd start. You're allowed to say it and stop there.

Pick one this week. Just one.

Scott
Real Talk &middot; ivoryroad.shop

---

## Email 4 — Day 7
**Subject:** The stuff you've been told
**Preview text:** And the stuff that's actually true

Somewhere along the way you picked up a list about yourself.

Some of it came from people who didn't know you. Some of it came from one bad day you never stopped replaying. Some of it you've said about yourself so many times it started sounding like a fact.

It isn't a fact.

The Identity and Truth page has two columns. One for what you've believed. One for what's true. Loved on the hard days. More than what people think. Not your worst mistake.

Write the lies down. They get smaller on paper. They're bigger when they only live in your head.

Scott
Real Talk &middot; ivoryroad.shop

---

## Email 5 — Day 10
**Subject:** You don't need the right words
**Preview text:** One sentence counts

A lot of guys don't pray because they figure they'll do it wrong.

Too short. Too plain. Too much like just talking.

That's still prayer.

God, right now I feel ___. God, I need help with ___. God, thank You for ___.

That's the whole page. Four lines. You can do it in the car or lying in bed with your eyes open.

The scripture cards are in there too. Cut them out, keep the ones you need, share the rest. That's what they're for.

Scott
Real Talk &middot; ivoryroad.shop

---

## Email 6 — Day 14
**Subject:** Where this came from
**Preview text:** The book, if you want it

Those pages came out of a book I wrote for guys your age.

**Real Talk: Becoming Who God Made You to Be.** Twelve short chapters on identity, emotions, and faith that isn't fake. It's written to you, not about you, and not in the voice adults use when they're trying to relate.

You can read a chapter in ten minutes.

[Find Real Talk on Amazon]

If you want it, show this to your mom or dad, or get it yourself.

And if you don't, keep the pages. Use the two or three that fit. That was always the point.

Scott
Real Talk &middot; ivoryroad.shop

---

*Link goes to `ivoryroad.shop/go/amazon/student/`, not straight to Amazon, so the
click is countable and carries the Attribution tag. The student book only. Do not
list the workbook, parent guide or leader guide here. One ask, and the parent
guide is not his to want.*

---

## After day 14

Do not run a monthly send to this list the way the parent list gets one. A teen
who stops hearing from you has moved on, and monthly mail to a sixteen year old
gets marked as spam, which costs the sending domain.

Better: let the sequence end. Send to this group only when there is something
real, a few times a year at most. The parent list is the one that gets kept warm.
