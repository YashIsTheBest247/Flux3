Drop your intro film here as:

    intro.mp4

It plays fullscreen over the landing page on a visitor's first arrival in a tab.

Rules it follows on its own:
  - never plays on phones or touch-only devices
  - never plays if the OS asks for reduced motion
  - plays once per tab session; "Replay intro" in the header runs it again
  - if this file is missing, the overlay removes itself instantly and the
    visitor just lands on the site

Practical notes:
  - h.264 / AAC in an .mp4 is the only combination every browser plays
  - 1920x1080 is plenty; it is object-cover'd to the viewport
  - keep it under ~10 MB and under ~15 seconds. It is served from the same
    container as the app, and a visitor waiting on a 60 MB download is
    a worse first impression than no intro at all
  - it starts MUTED because browsers block autoplay with sound; a
    "Sound off / Sound on" control sits bottom-left. Do not rely on the
    audio carrying the message
