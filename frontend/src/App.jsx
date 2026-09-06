import { useCallback, useEffect, useRef, useState } from 'react';
import { Header } from './components/Header.jsx';
import { Hero } from './components/Hero.jsx';
import { CreatorPanel } from './components/CreatorPanel.jsx';
import { InsightsSection } from './components/InsightsSection.jsx';
import { PipelineSection } from './components/PipelineSection.jsx';
import { LibrarySection } from './components/LibrarySection.jsx';
import { DevFooter } from './components/DevFooter.jsx';
import { pipelineSteps } from './data/options.js';
import { buildVideoPayload } from './lib/payload.js';
import { generateVideo, listVideos } from './api/videos.js';

const idlePipeline = {
    mode: 'idle',
    activeStepKey: null,
    statusText: 'Ready to render',
};

export function App() {
    const [videos, setVideos] = useState([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [isPolling, setIsPolling] = useState(false);
    const [pipeline, setPipeline] = useState(idlePipeline);
    const [searchQuery, setSearchQuery] = useState('');
    const [newFilename, setNewFilename] = useState(null);

    const pollTimerRef = useRef(null);
    const stepTimerRef = useRef(null);

    const refreshLibrary = useCallback(async () => {
        try {
            const response = await listVideos();
            setVideos(response);
            return response;
        } catch {
            setVideos([]);
            return [];
        }
    }, []);

    useEffect(() => {
        void refreshLibrary();
        return () => {
            if (pollTimerRef.current) window.clearInterval(pollTimerRef.current);
            if (stepTimerRef.current) window.clearTimeout(stepTimerRef.current);
        };
    }, [refreshLibrary]);

    function clearStepTimer() {
        if (stepTimerRef.current) {
            window.clearTimeout(stepTimerRef.current);
            stepTimerRef.current = null;
        }
    }

    function clearPollTimer() {
        if (pollTimerRef.current) {
            window.clearInterval(pollTimerRef.current);
            pollTimerRef.current = null;
        }
    }

    function runPipelineStep(stepIndex) {
        clearStepTimer();
        const step = pipelineSteps[stepIndex];
        if (!step) return;

        setPipeline({ mode: 'running', activeStepKey: step.key, statusText: step.statusText });

        if (stepIndex < pipelineSteps.length - 1) {
            stepTimerRef.current = window.setTimeout(() => {
                runPipelineStep(stepIndex + 1);
            }, step.durationMs);
        }
    }

    function completePipeline() {
        clearStepTimer();
        clearPollTimer();
        setIsPolling(false);
        setPipeline({ mode: 'complete', activeStepKey: null, statusText: 'Video ready' });
        scrollToSection('library');
    }

    function startPolling(filename) {
        clearPollTimer();
        setIsPolling(true);
        let attempts = 0;

        pollTimerRef.current = window.setInterval(async () => {
            attempts += 1;
            const refreshed = await refreshLibrary();
            const ready = filename ? refreshed.some((video) => video.name === filename) : false;

            if (ready) {
                completePipeline();
                return;
            }

            if (attempts >= 24) {
                clearPollTimer();
                setIsPolling(false);
                setPipeline(idlePipeline);
            }
        }, 5000);
    }

    async function handleGenerate(formValues) {
        setIsGenerating(true);
        setNewFilename(null);
        runPipelineStep(0);

        try {
            const payload = buildVideoPayload(formValues);
            const response = await generateVideo(payload);

            if (response?.success === false) {
                throw new Error(response.error || response.message || 'Generation failed.');
            }

            const filename = response.video_filename ?? null;
            setNewFilename(filename);
            await refreshLibrary();
            startPolling(filename);
        } catch (error) {
            clearStepTimer();
            setPipeline({
                mode: 'error',
                activeStepKey: null,
                statusText: 'Render request failed',
            });
            throw error;
        } finally {
            setIsGenerating(false);
        }
    }

    function scrollToSection(id) {
        if (id === 'top') {
            window.scrollTo({ top: 0, behavior: 'smooth' });
            return;
        }
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    return (
        <div className="flex min-h-screen flex-col">
            <Header onNavigate={scrollToSection} />
            <main className="flex-1">
                <Hero
                    onOpenApp={() => scrollToSection('creator')}
                    onDiscover={() => scrollToSection('insights')}
                />
                <CreatorPanel onGenerate={handleGenerate} isGenerating={isGenerating} />
                <InsightsSection />
                <PipelineSection
                    mode={pipeline.mode}
                    activeStepKey={pipeline.activeStepKey}
                    statusText={pipeline.statusText}
                />
                <LibrarySection
                    videos={videos}
                    searchQuery={searchQuery}
                    onSearchChange={setSearchQuery}
                    isGenerating={isGenerating}
                    isPolling={isPolling}
                    newFilename={newFilename}
                />
            </main>
            <DevFooter />
        </div>
    );
}
