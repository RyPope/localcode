import { Component, type ErrorInfo, type ReactNode } from "react";

interface State {
  error: Error | null;
}

/** Catches render errors in a page so one broken view doesn't blank the whole app. */
export default class ErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("localcode: render error", error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <main className="page" role="alert">
        <h1 className="title-1">Something went wrong</h1>
        <p className="note text-sm">{this.state.error.message}</p>
        <div className="row tight">
          <button className="btn primary" onClick={() => window.location.reload()}>
            Reload
          </button>
          <a className="btn" href="/">
            Back to problems
          </a>
        </div>
      </main>
    );
  }
}
