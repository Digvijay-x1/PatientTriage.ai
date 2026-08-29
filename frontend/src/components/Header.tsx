interface HeaderProps {
	onNewPatient?: () => void
}

function Header({ onNewPatient }: HeaderProps) {
	return (
		<header className="topbar">
			<div className="brand-lockup">
				<div className="brand-mark" aria-hidden="true">+</div>
				<div>
					<p className="brand-name">PatientTriage<span>.ai</span></p>
					<p className="brand-caption">Emergency coordination desk</p>
				</div>
			</div>
			<div className="topbar-actions">
				<span className="live-status"><span className="status-dot" />Live operations</span>
				<button className="primary-button" type="button" onClick={onNewPatient}>
					<span aria-hidden="true">+</span> New patient
				</button>
				<div className="user-avatar" aria-label="Signed in as Jordan Lee">JL</div>
			</div>
		</header>
	)
}

export default Header
