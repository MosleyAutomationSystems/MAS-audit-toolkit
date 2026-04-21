# plain_language.py
# C17 — Plain Language Report Generator
# Lookup table: check name → client-readable description.
# Keys match the "check" field values emitted by each check module.
# Add a new entry here whenever a new check module is built.
# reporter.py imports this — no other file should reference it directly.

PLAIN_LANGUAGE = {
    # ── Core Checks ──
    "Alt Text":
        "Some images on your site have no text description. "
        "Visitors who use screen readers — software that reads pages aloud for people who are blind or have low vision — "
        "will hear nothing when they reach those images.",

    "Heading Structure":
        "Your page headings are out of order or missing. "
        "Headings help visitors navigate a page the way a table of contents works in a book. "
        "Screen reader users rely on them to jump between sections quickly.",

    "Form Labels":
        "One or more form fields on your site have no label. "
        "A visitor using a screen reader would hear 'text field' or 'edit box' "
        "with no description of what information they are supposed to enter.",

    "Language Attribute":
        "Your page does not declare what language it is written in. "
        "Screen readers use this to pronounce words correctly. "
        "Without it, a Spanish-speaking user's screen reader may read English text with the wrong accent and rhythm.",

    "Tabindex Abuse":
        "Some elements on your site have been given a custom tab order that overrides the natural reading order. "
        "This can cause keyboard users to jump around the page in a confusing sequence "
        "instead of moving through content top to bottom.",

    "Empty Links":
        "Some links on your site have no visible or hidden label. "
        "A visitor using a screen reader would hear 'link' with no description of where the link goes.",

    "Empty Buttons":
        "Some buttons on your site have no label. "
        "A visitor using a screen reader would hear 'button' with no way to know what pressing it does.",

    "Autoplay Media":
        "Audio or video on your site starts playing automatically when the page loads. "
        "This can interfere with screen readers, which also use audio. "
        "It can also be disorienting or distressing for visitors with certain disabilities.",

    "PDF Link Warning":
        "Some links on your site open a PDF file without warning the visitor. "
        "PDFs open in a different application, which can be disorienting — "
        "especially for users who rely on keyboard navigation or screen readers.",

    "Page Title":
        "Your page is missing a title — the text that appears in the browser tab. "
        "Screen readers announce the page title as soon as a page loads. "
        "Without one, visitors have no immediate way to confirm they are on the right page.",

    "Duplicate IDs":
        "Your page has elements that share the same ID. "
        "IDs are supposed to be unique identifiers. "
        "When they are duplicated, assistive technologies and browsers may get confused "
        "about which element to interact with.",

    "Landmark Roles":
        "Your page is missing structural landmarks like a navigation area, main content area, or footer. "
        "Screen reader users use these landmarks to jump directly to the part of the page they need "
        "instead of listening to everything from the top.",

    "Skip Navigation Link":
        "Your page has no 'skip to main content' link. "
        "Keyboard users and screen reader users must Tab through every menu item on every page load "
        "before reaching the main content. A skip link lets them jump past repeated navigation instantly.",

    "Accessibility Patterns":
        "Your site contains one or more common accessibility patterns that are known to cause problems — "
        "such as links with vague labels like 'click here', form fields using placeholder text as a label, "
        "or interactive behavior attached to elements that are not designed to be interactive.",

    # ── Platform Detection ──
    "Platform Detection":
        "Your website is built on a platform that limits what can be changed. "
        "Some of the issues found in this report cannot be fixed without moving to a different platform. "
        "Those issues are marked as platform-restricted in the detailed findings.",

    # ── Viewport / Mobile ──
    "Viewport Meta":
        "Your site is preventing users from zooming in on mobile devices. "
        "Visitors with low vision rely on the ability to zoom to read text at a comfortable size. "
        "Blocking zoom is a direct barrier for those users.",

    "Touch Target CSS":
        "Some interactive elements on your site — buttons, links, or form fields — "
        "are too small to tap accurately on a touchscreen. "
        "This affects visitors with motor impairments, tremor, or reduced hand precision.",

    # ── Tables ──
    "Table Scope Attributes":
        "Some tables on your site are missing column or row headers. "
        "Without headers, a screen reader user cannot tell which column or row a data cell belongs to — "
        "like receiving a spreadsheet with no column names.",

    # ── Media ──
    "Figure/Figcaption":
        "Some images or figures on your site have no caption or description attached. "
        "Visitors who cannot see the image have no context for what it shows or why it is there.",

    "Animated GIF Detection":
        "Your site contains animated images that cannot be paused. "
        "For visitors with epilepsy or vestibular disorders, moving content can trigger "
        "discomfort, disorientation, or in some cases a medical episode.",

    "Muted Autoplay Extension":
        "Your site has video or audio that plays automatically and is not muted. "
        "This can interrupt screen readers and be startling or distressing for visitors "
        "with sensory sensitivities.",

    "Background Audio":
        "Your site plays audio in the background without an obvious way to pause or stop it. "
        "Screen reader users may be unable to hear their assistive technology over the background audio.",

    # ── Frames ──
    "iframe Title":
        "One or more embedded frames on your site have no label. "
        "A screen reader user would hear 'frame' with no description of what it contains — "
        "such as a map, a reservation widget, or a video player.",

    # ── SVG ──
    "SVG Accessibility":
        "Some icons or graphics on your site are not labeled for assistive technologies. "
        "Screen readers cannot describe them, so visitors who are blind have no information "
        "about what those graphics represent.",

    # ── Focus ──
    "Outline:none Detection":
        "The visible focus indicator has been removed from some elements on your site. "
        "Keyboard users rely on the focus outline to see which element is currently selected "
        "as they Tab through the page. Without it, they are navigating blind.",

    # ── Forms ──
    "Fieldset/Legend":
        "Some groups of related form fields — such as a set of radio buttons or checkboxes — "
        "are not labeled as a group. Screen reader users may not understand how the individual "
        "options relate to each other.",

    "Autocomplete Attribute":
        "Some form fields that collect personal information — such as name, email, or address — "
        "are missing autocomplete attributes. These attributes allow browsers to fill in "
        "information automatically, which is especially helpful for users with motor impairments "
        "or cognitive disabilities.",

    "Success Message":
        "Your site does not clearly confirm when a form has been submitted successfully. "
        "Screen reader users may not know whether their submission went through.",

    # ── Navigation ──
    "Multiple Nav Label":
        "Your site has more than one navigation menu but they are not labeled differently. "
        "A screen reader user cannot tell the primary navigation from a secondary or footer navigation "
        "without a distinguishing label on each.",

    "Skip Link Target Validation":
        "Your site has a 'skip to main content' link, but the destination it points to does not exist. "
        "Keyboard users who activate the skip link will not actually skip anything — "
        "the link is broken.",

    "Main Uniqueness":
        "Your page has more than one main content area defined. "
        "There should only be one. Screen readers use this landmark to orient users — "
        "having two creates confusion about where the primary content is.",

    # ── Language ──
    "Lang on Language Switches":
        "Your site contains content in more than one language, but the language "
        "is not declared on the individual sections. Screen readers will mispronounce "
        "words in the secondary language.",

    # ── Text ──
    "Small Text Detection":
        "Some text on your site is smaller than the recommended minimum size. "
        "This can be difficult or impossible to read for visitors with low vision, "
        "even with corrective lenses.",

    "Justified Text Detection":
        "Some text on your site uses full justification, which creates uneven gaps between words. "
        "This makes reading harder for visitors with dyslexia.",

    "All-Caps Text Detection":
        "Some text on your site is set in all capital letters using a CSS style. "
        "While it looks the same to sighted users, screen readers may read each letter individually — "
        "'W-E-L-C-O-M-E' instead of 'Welcome.'",

    # ── Link Warnings ──
    "Mailto Link Warning":
        "Some links on your site open an email client without warning. "
        "Visitors who do not have an email client configured may click the link "
        "and nothing will happen — with no explanation.",

    "Document Link Warning":
        "Some links on your site open a Word document, spreadsheet, or presentation file "
        "without warning the visitor. These files open in a separate application, "
        "which can be disorienting for keyboard and screen reader users.",

    # ── ARIA ──
    "aria-hidden on Focusable Elements":
        "Some elements on your site are hidden from screen readers but can still be "
        "reached by pressing Tab. A keyboard user can land on something that "
        "their screen reader will not describe — a silent, invisible dead end.",

    "aria-required Consistency":
        "Some form fields are marked as required in one way but not another. "
        "This inconsistency can cause screen readers to give incorrect information "
        "about which fields must be filled in before submitting.",

    "aria-describedby Orphan":
        "Some elements reference a description that does not exist on the page. "
        "This is like a footnote number that points to a page with no footnote — "
        "the reference leads nowhere.",

    "ARIA Role Validity":
        "Some elements on your site have invalid or unrecognized accessibility roles. "
        "Assistive technologies will not know how to handle them, which can cause "
        "unpredictable behavior for screen reader users.",

    # ── Image Maps ──
    "Image Map":
        "Your site has a clickable image map where one or more clickable areas "
        "have no text description. Screen reader users cannot tell what those areas do.",

    # ── Direction ──
    "RTL Direction":
        "Your site appears to contain right-to-left language content — such as Arabic or Hebrew — "
        "without declaring the reading direction. Text may display in the wrong order "
        "or be read incorrectly by assistive technologies.",

    # ── Meta / Technical ──
    "Meta Description":
        "Your page is missing a meta description — a short summary that appears in search results. "
        "While not a direct accessibility barrier, it helps users decide whether your page "
        "is the right one before they visit it.",

    "Robots Meta":
        "One or more pages on your site may be hidden from search engines. "
        "This is noted for your awareness — it may be intentional, "
        "or it may be preventing the wrong pages from being indexed.",

    "Mixed Content":
        "Your site loads some resources — images, scripts, or stylesheets — "
        "over an insecure connection even though your site uses HTTPS. "
        "Browsers may block these resources, causing parts of your page to not load.",

    "Third-Party Script Risk":
        "Your site loads scripts from external providers such as analytics or advertising tools. "
        "These scripts are noted for awareness — they can affect page performance and "
        "introduce content you do not directly control.",

    # ── Headers / Security ──
    "HTTP Header Analysis":
        "Your site is missing one or more recommended security headers. "
        "These are technical settings that tell browsers how to handle your site safely. "
        "Missing headers are noted as a best-practice risk indicator.",

    # ── Carousel ──
    "Carousel/Slider Autoplay":
        "Your site has a slideshow or carousel that advances automatically "
        "without a way to pause it. This can be disorienting for users with cognitive disabilities "
        "and can trigger discomfort for users with vestibular disorders.",

        # ── ARIA Live ──
    "aria-live Region Detection":
        "Your site may have areas that update dynamically — such as error messages, "
        "notifications, or status updates — without notifying screen reader users. "
        "When content changes on a page without a full reload, screen readers need "
        "a specific signal to announce the update. Without it, blind and low-vision "
        "users miss the change entirely.",
}