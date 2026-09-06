import { media } from '../data/media.js';

/**
 * The narrative middle of the page.
 *
 * Everything here is presentation: a two-tone serif statement, one anchoring
 * photograph, the run of things Flux actually does, and the numbers. The
 * working controls live below it. Splitting them that way means someone who
 * lands cold reads what this is before being asked to choose anything.
 */
export function Editorial({ onNavigate, activeProfileName }) {
    return (
        <>
            {/* ---------------------------------------------- statement -- */}
            <section className="px-3 sm:px-4">
                <div className="sheet mx-auto mt-3 w-full max-w-[1560px] px-5 pb-16 pt-16 sm:mt-4 sm:px-10 sm:pb-20 sm:pt-24">
                    <h2 className="display reveal mx-auto max-w-4xl text-center text-display-lg">
                        Creator <span className="text-accentsoft">Autopilot</span>
                    </h2>

                    {/* Faces flanking the sub-headline, as in the reference. They are
                        decorative, so they carry no alt text and no interaction. */}
                    {/* The avatars are positioned against a box WIDER than the
                        text column, so they sit in the margin instead of on top
                        of the first word. They also only appear from lg up,
                        where that margin actually exists. */}
                    <div className="relative mx-auto mt-12 max-w-4xl">
                        <img
                            src={media.team}
                            alt=""
                            className="absolute left-0 top-1 hidden h-16 w-16 rounded-full object-cover ring-4 ring-panel lg:block"
                        />
                        <img
                            src={media.studio}
                            alt=""
                            className="absolute right-0 top-24 hidden h-16 w-16 rounded-full object-cover ring-4 ring-panel lg:block"
                        />
                        <p className="display reveal mx-auto max-w-2xl text-center text-2xl leading-[1.35] sm:text-[1.75rem]">
                            Pick the kind of channel you run, and Flux finds what is
                            trending in it, writes it, voices it, captions it and publishes
                            it — on a schedule
                        </p>
                    </div>

                    {/* ------------------------------------- about card -- */}
                    <div className="reveal mt-16 grid gap-0 overflow-hidden rounded-[1.25rem] border border-tint/10 md:grid-cols-2">
                        <div className="media aspect-[4/3] md:aspect-auto">
                            <img src={media.editing} alt="A video edit timeline on a studio monitor" />
                            <span className="absolute bottom-4 left-4 rounded-lg bg-panel/95 px-3 py-1.5 text-xs backdrop-blur">
                                <span className="block font-medium text-txt">The other half</span>
                                <span className="block text-[0.68rem] text-faint">4–6 hrs / week</span>
                            </span>
                        </div>

                        <div className="flex flex-col justify-center gap-4 p-7 sm:p-10">
                            <span className="eyebrow">What it does</span>
                            <h3 className="display text-2xl">Two ways in, one pipeline</h3>
                            <p className="text-sm leading-relaxed text-muted">
                                Let it run on its own — it scans your niche's trend sources,
                                ranks what is actually moving, and produces a finished vertical
                                short. Or upload something you already made and get it back
                                titled, tagged, thumbnailed, captioned and published.
                            </p>
                            <p className="text-sm leading-relaxed text-muted">
                                Your uploaded file is never re-encoded. One frame comes out for
                                the thumbnail, the audio is transcribed to a caption track, and
                                the original bytes are what reach YouTube.
                            </p>
                            <div className="mt-2 flex flex-wrap gap-2">
                                <button type="button" onClick={() => onNavigate?.('channel')} className="btn-light">
                                    Choose a channel
                                </button>
                                <button type="button" onClick={() => onNavigate?.('upload')} className="btn-ghost">
                                    Upload a video
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* ------------------------------------- pill row ----
                        The filled pill is the channel type currently selected.
                        These alternated fills at first purely for visual rhythm,
                        which looked like it encoded something and did not - so
                        now it does, and each pill jumps to the picker. */}
                    <div className="reveal mt-10 flex flex-wrap justify-center gap-2.5">
                        {[
                            'Tech News',
                            'Markets & Money',
                            'Gaming',
                            'Fitness & Health',
                            'Entertainment',
                            'Science & Curiosity',
                        ].map((name) => {
                            const isActive = name === activeProfileName;
                            return (
                                <button
                                    key={name}
                                    type="button"
                                    onClick={() => onNavigate?.('channel')}
                                    aria-current={isActive ? 'true' : undefined}
                                    className={isActive ? 'pill-solid' : 'pill-quiet'}
                                >
                                    {isActive ? (
                                        <span className="h-1.5 w-1.5 rounded-full bg-accentsoft" aria-hidden="true" />
                                    ) : null}
                                    {name}
                                </button>
                            );
                        })}
                    </div>
                </div>
            </section>

            {/* ---------------------------------------------- services --- */}
            <section className="px-3 sm:px-4">
                <div className="mx-auto mt-3 w-full max-w-[1560px] px-1 pb-4 pt-16 sm:mt-4 sm:pt-20">
                    <div className="flex flex-wrap items-end justify-between gap-4 px-4 sm:px-6">
                        <h2 className="display reveal max-w-lg text-display-md">
                            The repetitive half,
                            <br />
                            handled
                        </h2>
                        <span className="eyebrow pb-2">What runs for you</span>
                    </div>

                    <div className="mt-9 grid gap-3 px-1 sm:grid-cols-2 lg:grid-cols-3">
                        {[
                            {
                                image: media.trends,
                                alt: 'A newspaper front page',
                                title: 'Finds the story',
                                body: 'Google Trends, Reddit, Hacker News, YouTube’s own chart and RSS — merged, de-duplicated and ranked.',
                                target: 'channel',
                            },
                            {
                                image: media.writing,
                                alt: 'A typewriter with a page in it',
                                title: 'Writes the packaging',
                                body: 'Three title options, a description with the hook in line one, twenty search tags and hashtags.',
                                target: 'upload',
                            },
                            {
                                image: media.overnight,
                                alt: 'A city skyline at night',
                                title: 'Publishes while you sleep',
                                body: 'On your channel’s own schedule, with the thumbnail and caption track attached after upload.',
                                target: 'publishing',
                            },
                        ].map((card, index) => (
                            <button
                                key={card.title}
                                type="button"
                                onClick={() => onNavigate?.(card.target)}
                                style={{ transitionDelay: `${index * 70}ms` }}
                                className="reveal media group aspect-[4/5] rounded-[1.25rem] text-left"
                            >
                                <img src={card.image} alt={card.alt} />
                                <span className="absolute inset-0 scrim" />

                                <span className="absolute inset-x-0 bottom-0 p-5 sm:p-6">
                                    <span className="display block text-lg text-white">{card.title}</span>
                                    {/* Collapsed until hover: the grid reads as three clean
                                        photographs at rest, and explains itself on approach. */}
                                    <span className="grid grid-rows-[0fr] transition-[grid-template-rows] duration-500 ease-out group-hover:grid-rows-[1fr] group-focus-visible:grid-rows-[1fr]">
                                        <span className="overflow-hidden">
                                            <span className="block pt-2 text-[0.8rem] leading-relaxed text-white/75">
                                                {card.body}
                                            </span>
                                        </span>
                                    </span>
                                </span>

                                <span className="absolute right-5 top-5 grid h-9 w-9 place-items-center rounded-full bg-white/90 text-[#12100E] transition-transform duration-300 group-hover:rotate-45">
                                    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M7 17 17 7M9 7h8v8" />
                                    </svg>
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            </section>

            {/* ---------------------------------------------- numbers ---- */}
            <section className="px-3 sm:px-4">
                <div className="relative mx-auto mt-6 w-full max-w-[1560px] overflow-hidden rounded-[1.5rem] bg-[#3B2F26] grain sm:rounded-[2rem]">
                    <img
                        src={media.analytics}
                        alt=""
                        className="absolute inset-0 h-full w-full object-cover opacity-[0.14]"
                    />
                    <div className="relative px-6 py-14 text-center sm:px-10 sm:py-20">
                        <h2 className="display reveal mx-auto max-w-2xl text-2xl leading-snug text-[#F5EFE6] sm:text-[2rem]">
                            The work that never made anything better,
                            <br className="hidden sm:block" /> done without you
                        </h2>

                        <dl className="mx-auto mt-12 grid max-w-3xl grid-cols-2 gap-8 sm:grid-cols-4">
                            {[
                                ['6', 'channel types'],
                                ['5', 'trend sources'],
                                ['0', 're-encodes'],
                                ['~2 min', 'per video'],
                            ].map(([value, label]) => (
                                <div key={label} className="reveal">
                                    <dt className="display text-3xl text-[#F5EFE6] sm:text-4xl">{value}</dt>
                                    <dd className="mt-1.5 text-[0.68rem] uppercase tracking-[0.14em] text-[#C6B49C]">
                                        {label}
                                    </dd>
                                </div>
                            ))}
                        </dl>
                    </div>
                </div>
            </section>
        </>
    );
}
