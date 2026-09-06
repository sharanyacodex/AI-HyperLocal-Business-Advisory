interface SectionHeadingProps {
  title: string;
  description?: string;
}

export function SectionHeading({ title, description }: SectionHeadingProps) {
  return (
    <div className="mb-6">
      <h2 className="text-xl font-semibold text-navy">{title}</h2>
      {description && (
        <p className="mt-1 text-sm text-navy/60 font-body">{description}</p>
      )}
    </div>
  );
}
