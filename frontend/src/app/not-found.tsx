export default function NotFound() {
  return (
    <div className="card">
      <h1 className="text-lg font-medium">Page not found</h1>
      <p className="mt-2 text-sm text-white/50">The page you're looking for doesn't exist.</p>
      <a href="/" className="mt-4 inline-block text-sm text-accent hover:underline">
        Back to dashboard
      </a>
    </div>
  );
}
