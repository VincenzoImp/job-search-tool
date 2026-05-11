import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "../../components/ui/badge";
import { Input } from "../../components/ui/input";
import { jobsQuery } from "./jobQueries";

export function JobsPage() {
  const [text, setText] = useState("");
  const params = useMemo(
    () => ({ limit: 50, offset: 0, sort: "score" as const, text: text || undefined }),
    [text]
  );
  const { data, isLoading, isError } = useQuery(jobsQuery(params));

  return (
    <section className="workspace" aria-label="Jobs">
      <div className="toolbar">
        <label className="search-field">
          <Search aria-hidden="true" size={18} />
          <Input
            aria-label="Search jobs"
            value={text}
            onChange={(event) => setText(event.target.value)}
            placeholder="Search title, company, location"
          />
        </label>
        <Badge>{data?.total ?? 0} jobs</Badge>
      </div>

      <div className="table-shell">
        <div className="table-header" role="row">
          <span>Score</span>
          <span>Role</span>
          <span>Company</span>
          <span>Site</span>
          <span>Status</span>
        </div>

        {isLoading ? <div className="table-state">Loading jobs</div> : null}
        {isError ? <div className="table-state">Unable to load jobs</div> : null}

        {data?.items.map((job) => (
          <a className="table-row" href={job.job_url ?? "#"} key={job.job_id}>
            <strong>{job.relevance_score}</strong>
            <span>{job.title}</span>
            <span>{job.company}</span>
            <span>{job.site ?? "unknown"}</span>
            <span>
              {job.applied ? <Badge tone="good">Applied</Badge> : null}
              {job.bookmarked ? <Badge tone="warning">Saved</Badge> : null}
              {!job.applied && !job.bookmarked ? <Badge>Open</Badge> : null}
            </span>
          </a>
        ))}
      </div>
    </section>
  );
}
