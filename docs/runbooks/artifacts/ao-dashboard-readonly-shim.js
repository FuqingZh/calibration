const dashboardPort = Number(window.location.port);

const readDaemonStatus = async () => {
	try {
		const response = await fetch("/dashboard-health", { cache: "no-store" });
		if (!response.ok) {
			throw new Error(`AO readiness returned HTTP ${response.status}`);
		}
		return { state: "ready", port: dashboardPort };
	} catch (error) {
		return {
			state: "error",
			code: "daemon_unreachable",
			message: error instanceof Error ? error.message : "AO readiness failed",
		};
	}
};

const subscribeDaemonStatus = (listener) => {
	let active = true;
	let previous = "";
	const refresh = async () => {
		const status = await readDaemonStatus();
		const serialized = JSON.stringify(status);
		if (active && serialized !== previous) {
			previous = serialized;
			listener(status);
		}
	};
	void refresh();
	const timer = window.setInterval(refresh, 5000);
	return () => {
		active = false;
		window.clearInterval(timer);
	};
};

window.ao = {
	app: {
		getVersion: async () => "0.11.1",
		openExternal: async (url) => window.open(url, "_blank", "noopener,noreferrer"),
		onNewSessionShortcut: () => () => {},
		onKeyboardShortcutsHelp: () => () => {},
		onNewShellTerminalShortcut: () => () => {},
		onOpenSettingsShortcut: () => () => {},
		onPreviousSessionShortcut: () => () => {},
		onNextSessionShortcut: () => () => {},
		onFocusTerminalShortcut: () => () => {},
	},
	daemon: {
		getStatus: readDaemonStatus,
		onStatus: subscribeDaemonStatus,
	},
	telemetry: { getBootstrap: async () => null },
	notifications: { show: async () => {}, onClick: () => () => {} },
	menu: { action: async () => {}, notifyShellFocus: () => {} },
	theme: { set: async () => {} },
	window: { isFullScreen: async () => false, onFullScreen: () => () => {}, setOverlay: async () => {} },
	appState: { getMigration: async () => ({ status: "complete" }), setMigration: async () => {} },
	updateSettings: { get: async () => ({}), set: async () => {} },
	keybindings: { get: async () => ({}), set: async (value) => value, setRecording: async () => {} },
	updates: {
		getStatus: async () => ({ state: "idle" }),
		check: async () => {},
		returnHome: async () => {},
		download: async () => {},
		install: async () => {},
		onStatus: () => () => {},
	},
	featureBuilds: { list: async () => [], getActive: async () => null },
	clipboard: { writeText: async (value) => navigator.clipboard.writeText(value), readText: async () => "" },
	browser: {
		ensure: async () => ({}),
		setBounds: () => {},
		navigate: async () => ({}),
		clear: async () => ({}),
		capture: async () => "",
		requestMirror: async () => false,
		goBack: async () => ({}),
		goForward: async () => ({}),
		reload: async () => ({}),
		stop: async () => ({}),
		destroy: () => {},
		setAnnotationMode: async () => {},
		onNavState: () => () => {},
		onAnnotationSubmit: () => () => {},
		onAnnotationCancel: () => () => {},
	},
	terminal: { saveDroppedFile: async () => { throw new Error("read-only Dashboard"); } },
};
