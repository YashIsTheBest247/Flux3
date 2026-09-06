import { insightStats } from '../data/options.js';

export function InsightsSection() {
    return (
        <section id="insights" className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
            <div className="mb-10 max-w-2xl">
                <h2 className="display text-3xl font-semibold sm:text-4xl">
                    Meet marvellous insights
                </h2>
                <p className="mt-3 text-sm text-muted lg:text-base">
                    Skip the manual timeline. Flux turns a topic into a finished, captioned video
                    while you watch each stage complete.
                </p>
            </div>

            <div className="grid gap-5 lg:grid-cols-3">
                {insightStats.map((stat) => (
                    <article key={stat.label} className="glass p-6">
                        <p className="display text-4xl font-semibold gradient-text">{stat.value}</p>
                        <p className="mt-4 text-sm font-medium text-txt">{stat.label}</p>
                        <p className="mt-1 text-sm text-muted">{stat.sub}</p>
                    </article>
                ))}
            </div>
        </section>
    );
}
