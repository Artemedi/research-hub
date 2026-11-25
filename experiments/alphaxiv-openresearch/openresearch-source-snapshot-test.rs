// Include only in a scratch copy of the pinned upstream src/compute.rs.
#[cfg(test)]
mod portability_lab {
    use crate::compute::SourceSnapshot;
    use crate::jobs::BackendDescriptor;
    use crate::local::model::{LocalExperiment, LocalProject};
    use crate::store::StoredRun;
    use std::fs;
    use std::path::{Path, PathBuf};
    use std::process::Command;

    fn checked(mut command: Command) -> String {
        let output = command.output().expect("start fixture utility");
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout).expect("ASCII fixture output")
    }

    fn git(root: &Path, args: &[&str]) -> String {
        let mut command = Command::new("git");
        command.current_dir(root).args(args);
        checked(command)
    }

    fn verify_archive(snapshot: &SourceSnapshot, expected: &str) {
        let mut hasher = Command::new("sha256sum");
        hasher.arg(&snapshot.path);
        assert_eq!(
            checked(hasher).split_ascii_whitespace().next(),
            Some(snapshot.digest.as_str())
        );
        assert_eq!(fs::metadata(&snapshot.path).unwrap().len(), snapshot.size);
        let mut list = Command::new("tar");
        list.arg("-tf").arg(&snapshot.path);
        assert_eq!(checked(list).trim(), "case.txt");
        let mut read = Command::new("tar");
        read.arg("-xOf").arg(&snapshot.path).arg("case.txt");
        assert_eq!(checked(read), expected);
    }

    #[test]
    fn snapshots_survive_checkout_loss_and_relocation() {
        let base = std::env::var_os("ORX_LAB_ROOT").expect("disposable lab path required");
        let base = PathBuf::from(base);
        for seed in [3, 7, 11, 19] {
            let case = base.join(format!("case-{seed}"));
            let origin = case.join("origin");
            fs::create_dir_all(&origin).unwrap();
            git(&origin, &["init", "-q", "-b", "lab"]);
            let expected = format!("Committed synthetic case {seed}.\n");
            fs::write(origin.join("case.txt"), &expected).unwrap();
            git(&origin, &["add", "--", "case.txt"]);
            git(&origin, &[
                "-c", "user.name=Lab", "-c", "user.email=lab@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "Synthetic case"
            ]);
            let revision = git(&origin, &["rev-parse", "HEAD"]).trim().to_owned();
            fs::write(origin.join("case.txt"), format!("Changed synthetic case {seed}.\n")).unwrap();
            let project = LocalProject {
                id: "lab".into(), name: "Lab".into(), slug: "lab".into(),
                github_owner: String::new(), github_repo: String::new(), github_sync_enabled: false,
                baseline_branch: "lab".into(), repo_path: origin.to_str().unwrap().into(),
                run_command: None, paper_id: None, created_at: 0, updated_at: 0,
            };
            let experiment = LocalExperiment {
                id: "exp".into(), project_id: "lab".into(), parent_experiment_id: None,
                slug: "lab".into(), branch_name: "lab".into(), title: None, description: None,
                run_command: "false".into(), agent_status: "idle".into(),
                created_at: 0, updated_at: 0, chat_session_id: None, archived: false,
            };
            std::env::set_var("ORX_DATA_DIR", case.join("initial"));
            let first = SourceSnapshot::create(&project, &experiment, false).unwrap();
            let second = SourceSnapshot::create(&project, &experiment, false).unwrap();
            assert_eq!(first.revision, revision);
            assert_eq!(first.digest, second.digest);
            assert_eq!(first.path, second.path);
            assert_eq!(fs::read_dir(first.path.parent().unwrap()).unwrap().count(), 1);
            verify_archive(&first, &expected);
            let mut descriptor = BackendDescriptor::parse(r#"{"kind":"local"}"#).unwrap();
            first.apply_to_descriptor(&mut descriptor);
            let recorded = StoredRun {
                id: "run".into(), experiment_id: "exp".into(), project_id: "lab".into(),
                status: "finished".into(), backend_json: descriptor.to_json(), command: "false".into(),
                created_at: 0, updated_at: 0, ended_at: None, exit_code: None,
                commit_sha: Some(revision), result_markdown: None, cancel_requested: false,
                cancel_reason: None, chat_session_id: None,
            };
            let descriptor = BackendDescriptor::parse(&recorded.backend_json).unwrap();
            fs::rename(&origin, case.join("offline-original")).unwrap();
            let retained = SourceSnapshot::from_run(&recorded, &descriptor).unwrap();
            verify_archive(&retained, &expected);
            let relocated = case.join("relocated");
            let destination = relocated.join("source-snapshots").join(first.path.file_name().unwrap());
            fs::create_dir_all(destination.parent().unwrap()).unwrap();
            fs::rename(&first.path, &destination).unwrap();
            std::env::set_var("ORX_DATA_DIR", &relocated);
            let restored = SourceSnapshot::from_run(&recorded, &descriptor).unwrap();
            assert_eq!(restored.path, destination);
            verify_archive(&restored, &expected);
            let mut changed = fs::read(&destination).unwrap();
            changed[0] ^= 1;
            fs::write(&destination, changed).unwrap();
            let error = SourceSnapshot::from_run(&recorded, &descriptor).unwrap_err();
            assert!(error.to_string().contains("digest check"));
        }
        println!(r#"ORX_SNAPSHOT_RESULT {{"cases":4,"committed_bytes_retained":4,"deduplicated":4,"retained_after_checkout_loss":4,"relocated_with_descriptor":4,"altered_archive_rejected":4}}"#);
    }
}
