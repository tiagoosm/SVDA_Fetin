import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

function Icon({ children, ...props }: IconProps) {
  return (
    <svg
      viewBox="0 0 24 24"
      width="24"
      height="24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  );
}

export const ArrowLeftIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M15 5l-7 7 7 7" />
  </Icon>
);

export const LogoutIcon = (props: IconProps) => (
  <Icon strokeWidth="2.2" {...props}>
    <path d="M10 4H5v16h5" />
    <path d="M15 8l4 4-4 4" />
    <path d="M19 12H9" />
  </Icon>
);

export const PlusIcon = (props: IconProps) => (
  <Icon width="20" height="20" strokeWidth="2.6" {...props}>
    <path d="M12 5v14M5 12h14" />
  </Icon>
);

export const SendIcon = (props: IconProps) => (
  <Icon fill="currentColor" stroke="none" {...props}>
    <path d="M3.4 20.4l17.4-8.4L3.4 3.6 3.3 10l12 2-12 2z" />
  </Icon>
);
